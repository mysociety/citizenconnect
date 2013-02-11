from django.db import models
from django.conf import settings

from citizenconnect.models import MessageModel

class Question(MessageModel):
    CATEGORY_CHOICES = (
        (u'services', u'Services'),
        (u'prescriptions', u'Prescriptions'),
        (u'general', u'General'),
    )
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
