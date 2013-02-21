from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.db import models

from citizenconnect.models import AuditedModel

# Create your models here.
class Organisation(AuditedModel,geomodels.Model):
    name = models.TextField()
    organisation_type = models.CharField(max_length=100, choices=settings.ORGANISATION_CHOICES)
    choices_id = models.IntegerField(db_index=True)
    ods_code = models.CharField(max_length=8, db_index=True, unique=True)
    point =  geomodels.PointField()
    objects = geomodels.GeoManager()

    @property
    def open_issues(self):
        return list(self.problem_set.open_problems()) + list(self.question_set.open_questions())

    def has_time_limits(self):
        if self.organisation_type == 'hospitals':
            return True
        else:
            return False

class Service(AuditedModel):
    name = models.TextField()
    service_code = models.TextField()
    organisation = models.ForeignKey(Organisation, related_name='services')

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("service_code", "organisation"),)
