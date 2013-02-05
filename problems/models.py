from django.db import models
from django.conf import settings

class AuditedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Problem(AuditedModel):
    ORGANISATION_CHOICES = (
        (u'hospital', u'Hospital'),
        (u'gppractice', u'GP'),
    )
    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
    )
    organisation_type = models.CharField(max_length=100, choices=ORGANISATION_CHOICES)
    organisation_id = models.IntegerField(db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    reporter_name = models.CharField(max_length=200)
    reporter_phone = models.CharField(max_length=50)
    reporter_email = models.CharField(max_length=254)
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
