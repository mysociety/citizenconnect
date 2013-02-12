from django.contrib.gis.db import models
from django.conf import settings

from citizenconnect.models import AuditedModel

# Create your models here.
class Organisation(AuditedModel, models.Model):
    name = models.TextField()
    organisation_type = models.CharField(max_length=100, choices=settings.ORGANISATION_CHOICES)
    choices_id = models.IntegerField(db_index=True)
    lon = models.FloatField()
    lat = models.FloatField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "organisations"
