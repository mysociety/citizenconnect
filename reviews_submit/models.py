from django.db import models

from citizenconnect.models import AuditedModel

class Review(AuditedModel):
    email = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    is_anonymous = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    month_year_of_visit = models.DateField()
    organisation = models.ForeignKey('organisations.Organisation')

class Rating(models.Model):
    review = models.ForeignKey('Review')
    question = models.ForeignKey('Question')
    answer = models.ForeignKey('AnswerOption')

class Question(models.Model):
    title = models.CharField(max_length=255)
    updated = models.DateTimeField()

class AnswerOption(models.Model):
    text = models.CharField(max_length=255)
    value = models.IntegerField()
    question = models.ForeignKey('Question')
