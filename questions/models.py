from django.db import models
from django.db.models import Q
from django.conf import settings

from citizenconnect.models import MessageModel

class QuestionManager(models.Manager):
    user_for_related_fields = True

    def open_questions(self):
        """
        Return only open problems
        """
        return super(QuestionManager, self).objects.all().filter(Q(status=Question.NEW) | Q(status=Question.ACKNOWLEDGED))

class Question(MessageModel):
    CATEGORY_CHOICES = (
        (u'services', u'Services'),
        (u'prescriptions', u'Prescriptions'),
        (u'general', u'General'),
    )

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2

    STATUS_CHOICES = (
        (NEW, 'Received but not acknowledged'),
        (ACKNOWLEDGED, 'Acknowledged but not answered'),
        (RESOLVED, 'Question answered'),
    )
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)
