from django.db import models
from django.conf import settings

from citizenconnect.models import MessageModel

class Problem(MessageModel):
    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
    )
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
