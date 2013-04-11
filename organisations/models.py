import logging
logger = logging.getLogger(__name__)

from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db import connection
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

from citizenconnect.models import AuditedModel

import auth
from .auth import user_in_group, user_in_groups, user_is_superuser, create_unique_username
from .metaphone import dm

class CCG(AuditedModel):
    name = models.TextField()
    code = models.CharField(max_length=8, db_index=True, unique=True)
    users = models.ManyToManyField(User, related_name='ccgs')

class Organisation(AuditedModel,geomodels.Model):

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

    # ISSUE-329: The `blank=True` should be removed when we are supplied with
    # email addresses for all the orgs
    # max_length set manually to make it RFC compliant (default of 75 is too short)
    # email may not be unique
    email = models.EmailField(max_length=254, blank=True)

    users = models.ManyToManyField(User, related_name='organisations')

    point =  geomodels.PointField()
    objects = geomodels.GeoManager()
    escalation_ccg = models.ForeignKey(CCG, blank=False, null=False, related_name='escalation_organisations')
    ccgs = models.ManyToManyField(CCG, related_name='organisations')

    # Calculated double_metaphone field, for search by provider name
    name_metaphone = models.TextField()

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
        if user_in_groups(user, [auth.NHS_SUPERUSERS, auth.CASE_HANDLERS]):
            return True

        # Providers in this organisation - YES
        if user in self.users.all():
            return True

        # CCG users for a CCG associated with this organisation - YES
        if user in User.objects.filter(ccgs__organisations=self).all():
            return True

        # Everyone else - NO
        return False


    def ensure_related_user_exists(self):
        """
        Check to see if this org has user. If not either find one or create one.

        Will raise a ValueError exception if the organisation has no user and
        has no email. ISSUE-329
        """

        # No need to create if there are already users
        if self.users.count(): return

        # We can't attach a user if we don't have an email address
        if not self.email: # ISSUE-329
            raise ValueError("Organisation needs an email to find/create related user")

        logger.info('Creating account for {0} (ODS code: {1})'.format(self.name,
                                                                       self.ods_code))

        try:
            user = User.objects.get(email=self.email)
        except User.DoesNotExist:
            user = User.objects.create_user(create_unique_username(self), self.email)

        # make sure user is in the right group. No-op if already a member.
        providers_group = Group.objects.get(pk=auth.PROVIDERS)
        user.groups.add(providers_group)

        # Add the user to this org
        self.users.add(user)

    def save(self, *args, **kwargs):
        """
        Overriden save to calculate double metaphones for name
        """
        # dm() expects unicode data, and gets upset with byte strings
        if isinstance(self.name, unicode):
            unicode_name = self.name
        else:
            unicode_name = unicode(self.name, encoding='utf-8', errors='ignore')
        name_metaphones = dm(unicode_name)
        self.name_metaphone = name_metaphones[0] # Ignoring the alternative for now
        super(Organisation, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

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
