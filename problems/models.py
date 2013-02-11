from django.db import models
from django.conf import settings

from citizenconnect.models import MessageModel

class Problem(MessageModel):
    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
    )

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2
    NOT_RESOLVED = 3

    STATUS_CHOICES = (
        (NEW, 'Received but not acknowledged'),
        (ACKNOWLEDGED, 'Acknowledged but not addressed'),
        (RESOLVED, 'Addressed - problem solved'),
        (NOT_RESOLVED, 'Addressed - unable to solve')
    )

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)
