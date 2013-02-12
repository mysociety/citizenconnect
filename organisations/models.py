from django.contrib.gis.db import models
from citizenconnect.models import AuditedModel

# Create your models here.
class Organisation(AuditedModel, models.Model):
    name = models.TextField(help_text='The name of the organisation')
    lon = models.FloatField()
    lat = models.FloatField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "organisations"
