"""Models for reviews submitted on the site."""

from django.utils import timezone
from django.db import models
from django.conf import settings

from citizenconnect.models import AuditedModel


class Review(AuditedModel):
    """A Review of a provider that has been left on the site."""
    # The email address of the reviewer
    email = models.EmailField(max_length=254)
    # Name the reviewer would like displayed next to their comment
    display_name = models.CharField(max_length=100)
    # Whether the reviewer would like to be anonymous
    is_anonymous = models.BooleanField(default=False)
    # Title the reviewer gave their review
    title = models.CharField(max_length=255, blank=False)
    # The text of the review
    comment = models.TextField(blank=False)
    # When the reviewer visited the Organisation they're reviewing
    month_year_of_visit = models.DateField()
    # Which organisation this is reviewing
    organisation = models.ForeignKey('organisations.Organisation', related_name='submitted_reviews')
    # When this review was sent to the NHS Choices API
    last_sent_to_api = models.DateTimeField(null=True, db_index=True)

    def __unicode__(self):
        """String representation of this Review"""
        return u"{0} - {1}".format(self.display_name, self.title)


class Rating(models.Model):
    """A rating of an aspect of an :model:`organisations.Organisation`,
    associated with a :model:`reviews_submit.Review`."""
    # The review this Rating is associated with
    review = models.ForeignKey('Review', related_name='ratings')
    # The question that was asked
    question = models.ForeignKey('Question', related_name='ratings')
    # The answer that was given
    answer = models.ForeignKey('Answer', blank=True, null=True)

    def __unicode__(self):
        """String representation of this Rating"""
        return u"{0} - {1}".format(self.question.title, self.answer.text)


class Question(models.Model):
    """Organisation type specific questions for ratings."""
    # The title of this question - the question text
    title = models.CharField(max_length=255)
    # The ID of this question as far as the NHS Choices API is concerned
    api_question_id = models.IntegerField()
    # Which type of organisation this question is for. Questions only apply to
    # a specific organisation_type, such as GPs or Hospitals
    org_type = models.CharField(max_length=100,
                                choices=settings.ORGANISATION_CHOICES,
                                blank=False)
    # When the question was last updated
    updated = models.DateTimeField(default=timezone.now)
    # Whether this question is one that has to be completed by the user
    is_required = models.BooleanField(default=False)

    def __unicode__(self):
        """String representation of this Question"""
        return self.title


class Answer(models.Model):
    """An answer for a :model:`reviews_submit.Rating`s
    :model:`reviews_display.Question`."""
    # The text of the answer
    text = models.CharField(max_length=255)
    # The id of the answer as far as the NHS Choices API is concerned
    api_answer_id = models.IntegerField()
    # The Question this answer is related to
    question = models.ForeignKey('Question', related_name='answers')

    # This is not provided by the NHS, but we need it internally to ensure
    # that the various answers are presented to the user in a sensible order.
    # Higher is better/more favourable. This is also the star rating to use in
    # the submission form. Note the unique_together constraint and the default
    # ordering in the Meta.
    star_rating = models.IntegerField(null=True)

    def __unicode__(self):
        """String representation of this Answer"""
        return self.text

    class Meta:
        unique_together = ('question', 'star_rating')
        ordering = ['star_rating']
