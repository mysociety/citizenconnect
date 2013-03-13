from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db import connection
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from citizenconnect.models import AuditedModel

class CCG(AuditedModel):
    name = models.TextField()
    code = models.CharField(max_length=8, db_index=True, unique=True)

class Organisation(AuditedModel,geomodels.Model):

    # Group id's for the user groups we care about when making decisions
    PROVIDERS = 1
    NHS_SUPERUSERS = 2
    MODERATORS = 3

    name = models.TextField()
    organisation_type = models.CharField(max_length=100, choices=settings.ORGANISATION_CHOICES)
    choices_id = models.IntegerField(db_index=True)
    ods_code = models.CharField(max_length=8, db_index=True, unique=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    county = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=10, blank=True)

    users = models.ManyToManyField(User, related_name='organisations')

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

    def has_services(self):
        if self.organisation_type == 'hospitals':
            return True
        else:
            return False

    def can_be_accessed_by(self, user):
        # Can a given user access this Organisation?

        # Deactivated users - NO
        if not user.is_active:
            return False

        # Django superusers - YES
        if user.is_superuser:
            return True

        # NHS Superusers or Moderators - YES
        if user.groups.filter(Q(pk=self.NHS_SUPERUSERS) | Q(pk=self.MODERATORS)).exists():
            return True

        # Providers in this organisation - YES
        if user in self.users.all():
            return True

        # Everyone else - NO
        return False

class Service(AuditedModel):
    name = models.TextField()
    service_code = models.TextField(db_index=True)
    organisation = models.ForeignKey(Organisation, related_name='services')

    def __unicode__(self):
        return self.name

    @classmethod
    def service_codes(cls):
        cursor = connection.cursor()
        cursor.execute("""SELECT distinct service_code, name
                          FROM organisations_service
                          ORDER BY name""")
        return cursor.fetchall()

    class Meta:
        unique_together = (("service_code", "organisation"),)

class SuperuserLogEntry(AuditedModel):
    """
    Logs of when an NHS Superuser accesses a page
    """
    user = models.ForeignKey(User, related_name='superuser_access_logs')
    path = models.TextField()
