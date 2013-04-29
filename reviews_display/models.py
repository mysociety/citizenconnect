from django.db import models

from organisations.models import Organisation
from citizenconnect.models import AuditedModel


class Review(AuditedModel):
    """
    A review of a provider which we have retrieved from the choices API. May
    have several ratings associated with.
    """

    # There are several API specific fields that we record in case they are needed in future

    # IDs for this review, and for the system where the review was created. Use Char
    # rather than number as it would appear that letters are used in some ids. The
    # max length should be fine as according to the API spec max is 10...
    api_posting_id            = models.CharField(max_length=20)
    api_postingorganisationid = models.CharField(max_length=20)

    # published and updated timestamps.
    api_published = models.DateTimeField()
    api_updated   = models.DateTimeField()

    # This is provided in the api and is meant to identify what the review is.
    API_CATEGORY_CHOICES = (
        ('comment',  'comment'),
        ('reply',    'reply'),
        ('deletion', 'deletion'),
    )
    api_category = models.CharField(max_length=10, choices=API_CATEGORY_CHOICES)

    # The organisation that this review concerns
    organisation = models.ForeignKey(Organisation)

    # The name to display for the author. May be 'Anonymous'
    author_display_name = models.TextField()
    title               = models.TextField()
    content             = models.TextField()

    # Fields we might also be able to get, but don't appear to be in API yet:
    # * visit_date
    # * is_anonymous
    # * in_response_to - if this is a 'reply' (or perhaps even a 'deletion') we should
    #                    know which comment it refers to.

    def __unicode__(self):
        return "{0}, {1} ({2})".format(self.title, self.author_display_name, self.id)



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

    review   = models.ForeignKey(Review)
    question = models.CharField(max_length=1000)  # e.g. "Was the area clean?"
    answer   = models.CharField(max_length=100)   # e.g. "Very clean"
    score    = models.IntegerField()              # e.g. 5

    def __unicode__(self):
        return "{0} ({1})".format(self.question, self.score)
