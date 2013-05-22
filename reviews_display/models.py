import datetime
from dateutil.parser import parse as dateutil_parse
import pytz

from django.conf import settings
from django.db import models
from django.forms.models import model_to_dict

from organisations.models import Organisation
from citizenconnect.models import AuditedModel


class OrganisationFromApiDoesNotExist(Exception):
    pass

class RepliedToReviewDoesNotExist(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class Review(AuditedModel):

    """
    A review of a provider which we have retrieved from the choices API. May
    have several ratings associated with.
    """

    # There are several API specific fields that we record in case they are
    # needed in future

    # IDs for this review, and for the system where the review was created. Use Char
    # rather than number as it would appear that letters are used in some ids. The
    # max length should be fine as according to the API spec max is 10...
    api_posting_id = models.CharField(max_length=20)
    api_postingorganisationid = models.CharField(max_length=20)

    # published and updated timestamps.
    api_published = models.DateTimeField()
    api_updated = models.DateTimeField()

    # This is provided in the api and is meant to identify what the review is.
    API_CATEGORY_CHOICES = (
        ('comment',  'comment'),
        ('reply',    'reply'),
        # ('deletion', 'deletion'),  # entry is just deleted from db atm
    )
    api_category = models.CharField(
        max_length=10,
        choices=API_CATEGORY_CHOICES
    )

    in_reply_to = models.ForeignKey('Review', related_name='replies', blank=True, null=True)

    # The organisation that this review concerns
    organisation = models.ForeignKey(Organisation, related_name='reviews')

    # The name to display for the author. May be 'Anonymous'
    author_display_name = models.TextField()
    title = models.TextField()

    # There are three content fields to mirror the comment structure seen in
    # the NHS API. For replies (which are just text) the content should go
    # into the 'content' field.
    content_liked = models.TextField(default="")
    content_improved = models.TextField(default="")
    content = models.TextField(default="")  # catch all

    # Fields we might also be able to get, but don't appear to be in API yet:
    # * visit_date
    # * is_anonymous
    # * in_response_to - if this is a 'reply' (or perhaps even a 'deletion') we should
    #                    know which comment it refers to.

    def __unicode__(self):
        return u"{0}, {1} ({2})".format(self.title, self.author_display_name, self.id)

    @classmethod
    def delete_old_reviews(cls):
        """
        Delete reviews that are older than
        NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS. This is based on the published
        date, it would be better if it was based on the visit date, but we are
        not supplied this in the API.
        """

        max_age_in_days = settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS
        max_age_timedelta = datetime.timedelta(days=max_age_in_days)
        oldest_permitted = datetime.datetime.now(pytz.utc) - max_age_timedelta

        cls.objects.filter(api_published__lte=oldest_permitted).delete()

    @classmethod
    def upsert_or_delete_from_api_data(cls, api_review):
        """

        Given a review scraped from the API creates or updates an entry in the
        database for it, and related reviews.

        If the organisation cannot be found (which is likely as initially not
        all orgs will be part of this project) then it will throw an
        OrganisationFromApiDoesNotExist exception.

        If the  category is deletion, or the published date is more than
        NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS days old, the entry is deleted

        """

        # For replies try to load the review they relate to. If not found raise
        # an exception. Because of the order that the API gives us results in
        # this might be quite common.
        if api_review['api_category'] == 'reply':
            try:
                api_review['in_reply_to'] = cls.objects.get(api_posting_id=api_review['in_reply_to_id'])
            except cls.DoesNotExist:
                raise RepliedToReviewDoesNotExist(
                    "Could not find review with api_posting_id of {0} for reply {1}".format(
                        api_review['in_reply_to_id'],
                        api_review['api_posting_id']
                    )
                )

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
            organisation = Organisation.objects.get(
                choices_id=api_review['organisation_choices_id'])
        except Organisation.DoesNotExist:
            raise OrganisationFromApiDoesNotExist(
                "Could not find organisation with choices_id = '{0}'".format(
                    api_review['organisation_choices_id']
                )
            )

        defaults = api_review.copy()
        del defaults['ratings']
        del defaults['organisation_choices_id']
        del defaults['in_reply_to_id']
        defaults['organisation'] = organisation

        review, created = cls.objects.get_or_create(
            defaults=defaults, **unique_args)

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


class Rating(AuditedModel):

    """
    A review of a provider, attached to a Review.

    This is a somewhat inelegant de-normalised way to store the ratings, ideally
    a RatingCategory model would have been used to store the questions and
    response wordings and that would have been linked to from each Rating.
    However the source of these ratings (the Choices API) does not (in the
    examples available at the time of writing) provide sufficient information to
    do this confidently. As we don't initially require aggregation of results,
    we want to be sure we display the correct data and disk is cheap we use this
    inefficient model.
    """

    review = models.ForeignKey(Review, related_name='ratings')
    question = models.CharField(max_length=1000)  # e.g. "Was the area clean?"
    answer = models.CharField(max_length=100)     # e.g. "Very clean"
    score = models.IntegerField()                 # e.g. 5

    def __unicode__(self):
        return u"{0} ({1})".format(self.question, self.score)
