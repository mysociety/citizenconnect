"""
Models for reviews submitted on the site.
"""

from django.utils import timezone
from django.db import models

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


class Rating(models.Model):

    """A rating of an aspect of the provider, associated with a Review."""

    review = models.ForeignKey('Review')
    question = models.ForeignKey('Question')
    answer = models.ForeignKey('Answer')


class Question(models.Model):

    """A multiple choice Question in a Review."""

    GPS = 'gps'
    HOSPITALS = 'hospitals'
    ORG_TYPE_CHOICES = (
        (GPS, 'GPs'),
        (HOSPITALS, 'Hospitals'),
    )

    title = models.CharField(max_length=255)
    api_question_id = models.IntegerField()
    org_type = models.CharField(max_length=100,
                                choices=ORG_TYPE_CHOICES,
                                blank=False)
    updated = models.DateTimeField(default=timezone.now)


class Answer(models.Model):

    """A single multiple choice answer for a Question."""

    text = models.CharField(max_length=255)
    api_answer_id = models.IntegerField()
    question = models.ForeignKey('Question')
