import datetime
from dateutil.parser import parse as dateutil_parse
import pytz

from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict
from django.utils.text import Truncator

from organisations.models import Organisation, OrganisationParent
from citizenconnect.models import AuditedModel


class OrganisationFromApiDoesNotExist(Exception):
    """Exception thrown when an :model:`organisations.Organisation` processed
    from the NHS Choices API is not found in the database."""
    pass


class RepliedToReviewDoesNotExist(Exception):
    """Exception thrown when the :model:`reviews_display.Review` that a reply
    processed from the NHS Choices API claims to be related to, is not found
    in the database."""
    def __init__(self, message):
        """Create an Exception with the given message"""
        self.message = message

    def __str__(self):
        """Return a string representation of the Exception"""
        return self.message


class Review(AuditedModel):
    """A review of an :model:`organisations.Organisation` which we have
    retrieved from the NHS Choices API.

    One Review may have several :model:`reviews_display.Rating`s associated
    with it.
    """

    # There are several API specific fields that we record in case they are
    # needed in future

    # IDs for this review, and for the system where the review was created. Use Char
    # rather than number as it would appear that letters are used in some ids. The
    # max length should be fine as according to the API spec max is 10...
    api_posting_id = models.CharField(max_length=20)
    api_postingorganisationid = models.CharField(max_length=20)

    # published and updated timestamps.
    api_published = models.DateTimeField(db_index=True)
    api_updated = models.DateTimeField()

    # This is provided in the api and is meant to identify what the review is.
    # i.e.: is it a review from the public, a reply to one from an organisation
    # or a review being marked as deleted.
    API_CATEGORY_CHOICES = (
        ('comment',  'comment'),
        ('reply',    'reply'),
        # ('deletion', 'deletion'),  # entry is just deleted from db atm
    )
    api_category = models.CharField(
        max_length=10,
        choices=API_CATEGORY_CHOICES
    )

    # Which Review this is replying to, if it's a reply
    in_reply_to = models.ForeignKey('Review', related_name='replies', blank=True, null=True)

    # The organisations that this review concerns - for Hospitals this will just be one
    # organisation, but for GP's the review comes in marked against the surgery and we need
    # to associate it with all of the GP's branches.
    organisations = models.ManyToManyField(Organisation, related_name='reviews')

    # The name to display for the author. May be 'Anonymous'
    author_display_name = models.TextField()
    # The title the reviewer gave
    title = models.TextField()

    # There are three content fields to mirror the comment structure seen in
    # the NHS API. For replies (which are just text) the content should go
    # into the 'content' field.
    content_liked = models.TextField(default="", blank=True)
    content_improved = models.TextField(default="", blank=True)
    content = models.TextField(default="", blank=True)  # catch all

    # Fields we might also be able to get, but don't appear to be in API yet:
    # * visit_date
    # * is_anonymous

    def __unicode__(self):
        """Return a string representation of the Review"""
        return u"{0}, {1} ({2})".format(self.title, self.author_display_name, self.id)

    @property
    def main_rating_score(self):
        """Return the score of the 'main' rating.

        The main rating is the "Friends and Family" rating which asks something
        like: "Would you recommend this organisation to your friends and Family
        """
        # TODO: There must be a better way to get the Friends and Family rating."""
        try:
            score = self.ratings.get(question='Friends and Family').score
        except Rating.DoesNotExist:
            score = None
        return score

    @property
    def summary(self):
        """Return a summary of the review's content field"""
        if self.content:
            return Truncator(self.content).words(20)
        else:
            # TODO - search through other fields for something useful to summarise
            return "See more..."

    @classmethod
    def delete_old_reviews(cls):
        """Delete reviews that are older than NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS.

        This is based on the published date, it would be better if it was
        based on the visit date, but we are not supplied this in the API.
        """

        max_age_in_days = settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS
        max_age_timedelta = datetime.timedelta(days=max_age_in_days)
        oldest_permitted = datetime.datetime.now(pytz.utc) - max_age_timedelta

        cls.objects.filter(api_published__lte=oldest_permitted).delete()

    @classmethod
    def upsert_or_delete_from_api_data(cls, api_review, organisation_type):
        """Create or update an entry in the database for a review from the API
        and related reviews.

        If the organisation cannot be found (which is likely as initially not
        all orgs will be part of this project) then it will throw an
        OrganisationFromApiDoesNotExist exception.

        If the  category is deletion, or the published date is more than
        NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS days old, the entry is deleted
        """

        unique_args = dict(
            api_posting_id=api_review['api_posting_id'],
            api_postingorganisationid=api_review['api_postingorganisationid']
        )

        max_age_in_days = settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS
        oldest_permitted = datetime.datetime.now() - datetime.timedelta(
            days=max_age_in_days)
        pub_date = dateutil_parse(api_review['api_published'], ignoretz=True)

        # If this is a deletion or published is too old then delete from the db
        if api_review['api_category'] == 'deletion' or pub_date <= oldest_permitted:
            try:
                cls.objects.get(**unique_args).delete()
            except cls.DoesNotExist:
                pass  # if it was not in db then no need to delete it
            return

        # Load the org. If not possible skip this review.
        try:
            # For a hospital, this is the org given in the api data,
            # for the GP, the data given is the id of the surgery, so we
            # need to get that org and then get all its' branches
            if organisation_type == "gppractices":
                gp_surgery = OrganisationParent.objects.get(
                    choices_id=api_review['organisation_choices_id']
                )
                organisations = list(gp_surgery.organisations.all())
            else:
                organisation = Organisation.objects.get(
                    choices_id=api_review['organisation_choices_id'])
                organisations = [organisation]
        except (Organisation.DoesNotExist, OrganisationParent.DoesNotExist):
            raise OrganisationFromApiDoesNotExist(
                "Could not find organisation with choices_id = '{0}'".format(
                    api_review['organisation_choices_id']
                )
            )

        # For replies try to load the review they relate to. If not found raise
        # an exception. Because of the order that the API gives us results in
        # this might be quite common.
        if api_review['api_category'] == 'reply':
            try:
                api_review['in_reply_to'] = cls.objects.get(api_posting_id=api_review['in_reply_to_id'],
                                                            api_postingorganisationid=api_review['in_reply_to_organisation_id'])
            except cls.DoesNotExist:
                raise RepliedToReviewDoesNotExist(
                    "Could not find review with api_posting_id of {0} for reply {1}".format(
                        api_review['in_reply_to_id'],
                        api_review['api_posting_id']
                    )
                )

        defaults = api_review.copy()
        del defaults['ratings']
        del defaults['organisation_choices_id']
        del defaults['in_reply_to_id']
        del defaults['in_reply_to_organisation_id']

        review, created = cls.objects.get_or_create(
            defaults=defaults, **unique_args)

        # Assign organisations
        # Assigning like this clears any existing relationships so it doesn't
        # matter if it was newly created or existed already
        review.organisations = organisations

        if not created:
            for field in defaults.keys():
                setattr(review, field, defaults[field])  # ick-ity yuck :(
            review.save()

        # check if the ratings have changed, if they have delete them all and
        # reinsert
        current_ratings = [
            model_to_dict(x, exclude=['id', 'review'])
            for x
            in review.ratings.all().order_by('question')
        ]

        if current_ratings != api_review['ratings']:
            review.ratings.all().delete()

        for rating in api_review['ratings']:
            review.ratings.create(**rating)

        return True

    class Meta:
        # The api_posting_id should be unique for the organisation that added
        # the review
        unique_together = (("api_posting_id", "api_postingorganisationid"),)


class Rating(AuditedModel):
    """A review of a provider, attached to a :model:`reviews_display.Review`.

    This is a somewhat inelegant de-normalised way to store the ratings, ideally
    a RatingCategory model would have been used to store the questions and
    response wordings and that would have been linked to from each Rating.
    However the source of these ratings (the Choices API) does not (in the
    examples available at the time of writing) provide sufficient information to
    do this confidently. As we don't initially require aggregation of results,
    we want to be sure we display the correct data and disk is cheap we use this
    inefficient model.
    """

    # Which review this Rating is attached to
    review = models.ForeignKey(Review, related_name='ratings')
    # The text of the question this rating posed, e.g. "Was the area clean?"
    question = models.CharField(max_length=1000, db_index=True)
    # The text of the answer the user selected, e.g. "Very clean"
    answer = models.CharField(max_length=100)
    # The numeric score of the answer selected, e.g. 5
    score = models.IntegerField()

    def __unicode__(self):
        """Return a string representation of the Rating"""
        return u"{0} ({1})".format(self.question, self.score)
