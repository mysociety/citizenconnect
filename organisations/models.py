import logging
logger = logging.getLogger(__name__)

from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.db import models
from django.db import connection
from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver

from citizenconnect.models import AuditedModel
from .mixins import MailSendMixin

from issues.models import Problem

import auth
from .auth import user_in_group, user_in_groups
from .metaphone import dm


class CCG(MailSendMixin, AuditedModel):
    name = models.TextField()
    code = models.CharField(max_length=8, db_index=True, unique=True)
    users = models.ManyToManyField(User, related_name='ccgs')

    # ISSUE-329: The `blank=True` should be removed when we are supplied with
    # email addresses for all the orgs
    # max_length set manually to make it RFC compliant (default of 75 is too short)
    # email may not be unique
    email = models.EmailField(max_length=254, blank=True)

    def default_user_group(self):
        """Group to ensure that users are members of"""
        return Group.objects.get(pk=auth.CCG)

    def can_be_accessed_by(self, user):
        """ Can a user access this ccg? """

        # Deactivated users - NO
        if not user.is_active:
            return False

        # Django superusers - YES
        if user.is_superuser:
            return True

        # NHS Superusers - YES
        if user_in_group(user, auth.NHS_SUPERUSERS):
            return True

        # Users in this ccg - YES
        if user in self.users.all():
            return True

        # Everyone else - NO
        return False

    @property
    def problem_set(self):
        return Problem.objects.filter(organisation__trust__in=self.organisation_parents.all())

    def __unicode__(self):
        return self.name


class OrganisationParent(MailSendMixin, AuditedModel):
    """
    Something that is the parent body of an Organisation.

    In the case of Hospitals or Clinics, this is an NHS Trust, in the
    case of GP Branches, this is the main surgery
    """
    name = models.TextField()
    code = models.CharField(max_length=8, db_index=True, unique=True)
    users = models.ManyToManyField(User, related_name='trusts')

    # ISSUE-329: The `blank=True` should be removed when we are supplied with
    # email addresses for all the trusts
    # max_length set manually to make it RFC compliant (default of 75 is too short)
    # email may not be unique
    email = models.EmailField(max_length=254, blank=True)
    secondary_email = models.EmailField(max_length=254, blank=True)

    # Which CCG this Parent should escalate problems too
    escalation_ccg = models.ForeignKey(CCG, blank=False, null=False, related_name='escalation_trusts')

    # Which CCGs commission services from this Parent.
    # This means that those CCGs will be able to see all the problems at
    # this parent's organisations.
    ccgs = models.ManyToManyField(CCG, related_name='organisation_parents')

    def can_be_accessed_by(self, user):
        """ Can a user access this trust? """

        # Deactivated users - NO
        if not user.is_active:
            return False

        # Django superusers - YES
        if user.is_superuser:
            return True

        # NHS Superusers, Moderators or customer contact centre users - YES
        if user_in_groups(user, [auth.NHS_SUPERUSERS,
                                 auth.CASE_HANDLERS,
                                 auth.CUSTOMER_CONTACT_CENTRE]):
            return True

        # Users in this Parent - YES
        if user in self.users.all():
            return True

        # CCG users for a CCG associated with this Parent - YES
        if user in User.objects.filter(ccgs__organisation_parents=self).all():
            return True

        # Everyone else - NO
        return False

    def default_user_group(self):
        """Group to ensure that users are members of"""
        return Group.objects.get(pk=auth.TRUSTS)

    @property
    def problem_set(self):
        return Problem.objects.filter(organisation__in=self.organisations.all())

    def __unicode__(self):
        return self.name


@receiver(post_save, sender=OrganisationParent)
def ensure_ccgs_contains_escalation_ccg(sender, **kwargs):
    """ post_save signal handler to ensure that trust.escalation_ccg is always in trust.ccgs """
    trust = kwargs['instance']
    if trust.escalation_ccg and trust.escalation_ccg not in trust.ccgs.all():
        trust.ccgs.add(trust.escalation_ccg)


class Organisation(AuditedModel, geomodels.Model):

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

    point = geomodels.PointField()
    objects = geomodels.GeoManager()

    # Which Trust this is in
    trust = models.ForeignKey(OrganisationParent, blank=False, null=False, related_name='organisations')

    # Calculated double_metaphone field, for search by provider name
    name_metaphone = models.TextField(editable=False)

    # Average review rating from "Would you recommend this provider to your friends and family?"
    average_recommendation_rating = models.FloatField(blank=True, null=True)

    @property
    def organisation_type_name(self):
        for code, label in settings.ORGANISATION_CHOICES:
            if code == self.organisation_type:
                return label

        # should never get here, but best to have a fallback
        return 'Not Known'

    @property
    def open_issues(self):
        return list(self.problem_set.open_problems())

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
        """ Can a given user access this Organisation? """
        # Access is controlled by the Trust
        return self.trust.can_be_accessed_by(user)

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
        self.name_metaphone = name_metaphones[0]  # Ignoring the alternative for now
        super(Organisation, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name


class Service(AuditedModel):
    name = models.TextField()
    service_code = models.TextField(db_index=True)
    organisation = models.ForeignKey(Organisation, related_name='services')

    @classmethod
    def service_codes(cls):
        cursor = connection.cursor()
        cursor.execute("""SELECT distinct service_code, name
                          FROM organisations_service
                          ORDER BY name""")
        return cursor.fetchall()

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("service_code", "organisation"),)


class SuperuserLogEntry(AuditedModel):
    """
    Logs of when an NHS Superuser accesses a page
    """
    user = models.ForeignKey(User, related_name='superuser_access_logs')
    path = models.TextField()
