"""
Models for reviews submitted on the site.
"""

from django.utils import timezone
from django.db import models
from django.conf import settings

from citizenconnect.models import AuditedModel


class Review(AuditedModel):

    """A Review of a provider that has been left on the site."""

    email = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    is_anonymous = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    month_year_of_visit = models.DateField()
    organisation = models.ForeignKey('organisations.Organisation')
    last_sent_to_api = models.DateTimeField(null=True)

    def __unicode__(self):
        return "{0} - {1}".format(self.display_name, self.title)


class Rating(models.Model):

    """A rating of an aspect of the provider, associated with a Review."""

    review = models.ForeignKey('Review')
    question = models.ForeignKey('Question')
    answer = models.ForeignKey('Answer', blank=True, null=True)

    def __unicode__(self):
        return "{0} - {1}".format(self.question.title, self.answer.text)


class Question(models.Model):

    """Organisations type specific questions for ratings."""

    title = models.CharField(max_length=255)
    api_question_id = models.IntegerField()
    org_type = models.CharField(max_length=100,
                                choices=settings.ORGANISATION_CHOICES,
                                blank=False)
    updated = models.DateTimeField(default=timezone.now)

    def __unicode__(self):
        return self.title


class Answer(models.Model):

    """An answer for a ratings question."""

    text = models.CharField(max_length=255)
    api_answer_id = models.IntegerField()
    question = models.ForeignKey('Question')

    def __unicode__(self):
        return self.text
