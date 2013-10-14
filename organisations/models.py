import logging
logger = logging.getLogger(__name__)
import csv

from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.db import models, connection, IntegrityError, transaction
from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.encoding import force_unicode

from citizenconnect.models import (
    AuditedModel,
    validate_file_extension,
    partitioned_upload_path_and_obfuscated_name
)
from .mixins import MailSendMixin

from issues.models import Problem

import auth
from .auth import user_in_groups
from .metaphone import dm

from sorl.thumbnail import ImageField as sorlImageField


class CCG(MailSendMixin, AuditedModel):
    """Stores Clinical Commissioning Groups.

    These groups commission services from Organisation Parents (usually
    Trusts), and are eventually responsible for them.
    """
    # Name of the CCG
    name = models.TextField()
    # Unique code for the CCG - called intermittently and ODS code or NACS
    # code by the NHS.
    code = models.CharField(max_length=8, db_index=True, unique=True)
    # Users who belong to this CCG
    users = models.ManyToManyField(User, related_name='ccgs')
    # Main contact email address for this CCG, if the site needs to send an
    # email address to it generally, rather than a specific user at the CCG.
    # max_length set manually to make it RFC compliant (default of 75 is
    # too short) email may not be unique - for example a catch-all address may
    # be used
    email = models.EmailField(max_length=254)

    def save(self, *args, **kwargs):
        """Overriden save to ensure email address is set."""
        if not self.email:
            raise ValidationError("email is required")

        super(CCG, self).save(*args, **kwargs)

    def default_user_group(self):
        """Group to ensure that this CCG's users are members of"""
        return Group.objects.get(pk=auth.CCG)

    def can_be_accessed_by(self, user):
        """Check whether a given user can access this ccg?"""

        # Deactivated users - NO
        if not user.is_active:
            return False

        # Django superusers - YES
        if user.is_superuser:
            return True

        # NHS Superusers, Case Handlers - YES
        if user_in_groups(user, [auth.NHS_SUPERUSERS, auth.CASE_HANDLERS]):
            return True

        # Users in this ccg - YES
        if user in self.users.all():
            return True

        # Everyone else - NO
        return False

    @property
    def problem_set(self):
        """Return the set of problems which "belong" to this CCG.

        What this means is problems reported against an Organisation whose
        Organisation Parent has this CCG marked as it's primary_ccg - i.e.:
        where this CCG is eventually responsible for the services it provides
        """
        return Problem.objects.filter(organisation__parent__in=self.organisation_parents.all())

    def __unicode__(self):
        return self.name


class FriendsAndFamilySurvey(AuditedModel):
    """Stores the monthly results of a survey conducted of patients in a
    particular ward of a hospital, or a particular NHS Trust"""

    # These three fields are so that we can foreign key to both Organisations and
    # OrganisationParents in one relation.
    # See: https://docs.djangoproject.com/en/1.4/ref/contrib/contenttypes/

    # These two fields effectively "id" the Organisation or OrganisationParent
    # that a survey is related to
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    # This will point to the Organisation or OrganisationParent we're related
    # to, but you can't use it in filter(), etc - it doesn't work like that.
    content_object = generic.GenericForeignKey()

    # The overall score (out of 100)
    overall_score = models.PositiveIntegerField()

    # Individual numbers for different responses
    extremely_likely = models.PositiveIntegerField()
    likely = models.PositiveIntegerField()
    neither = models.PositiveIntegerField()
    unlikely = models.PositiveIntegerField()
    extremely_unlikely = models.PositiveIntegerField()
    dont_know = models.PositiveIntegerField()

    # Where this survey was performed, usually a hospital ward such as A&E.
    # Trust survey's don't have this, hence it can be blank
    location = models.CharField(
        max_length=100,
        db_index=True,
        blank=True,
        choices=settings.SURVEY_LOCATION_CHOICES
    )

    # When this survey was taken. Really, this is just the month/year, the day
    # is irrelevant, but it's easier to sort and filter by date if we store it
    # in a DateField.
    date = models.DateField(db_index=True)

    @classmethod
    def location_display(cls, location):
        """Normal Django get_FOO_display only works on instances, not passed
        values."""

        # Copied from django.db.models.base._get_FIELD_display and tweaked a bit
        return force_unicode(
            dict(settings.SURVEY_LOCATION_CHOICES).get(location, location),
            strings_only=True
        )

    @classmethod
    def process_csv(cls, csv_file, month, content_type, location=None):
        """Process a csv file of multiple surveys for either a Site (hospital)
        or a Trust and create objects for them.

        Returns an array of the created models."""

        if content_type == "site" and location is None:
            raise ValueError("Location is required for site files.")

        if not content_type == 'site' and not content_type == 'trust':
            raise ValueError("Unknown content_type")

        created = []

        csv_reader = csv.DictReader(csv_file, delimiter=',', quotechar='"')
        for row in csv_reader:

            # Work out the content_object the survey is for
            content_object = None
            if content_type == "site":
                site_code = row['Site Code']
                try:
                    content_object = Organisation.objects.get(ods_code=site_code)
                except Organisation.DoesNotExist:
                    # TODO - should we just skip these?
                    raise ValueError("Organisation with site code: {0} ({1}) is not in the database.".format(site_code, row['Site Name']))
            else:
                code = row['Code']
                try:
                    content_object = OrganisationParent.objects.get(code=code)
                except OrganisationParent.DoesNotExist:
                    # TODO - should we just skip these?
                    raise ValueError("OrganisationParent with code: {0} ({1}) is not in the database.".format(code, row['Name']))

            try:
                overall_score = int(row['Friends and Family Test Score'])
                extremely_likely = int(row['Extremely Likely'])
                likely = int(row['Likely'])
                neither = int(row['Neither'])
                unlikely = int(row['Unlikely'])
                extremely_unlikely = int(row['Extremely Unlikely'])
                dont_know = int(row['Don\'t Know'])
            except (KeyError, ValueError):
                raise ValueError("Could not retrieve one of the score fields from the csv for: {0}, or the data is not a valid score.".format(content_object.name))

            try:
                survey = FriendsAndFamilySurvey(
                    content_object=content_object,
                    overall_score=overall_score,
                    extremely_likely=extremely_likely,
                    likely=likely,
                    neither=neither,
                    unlikely=unlikely,
                    extremely_unlikely=extremely_unlikely,
                    dont_know=dont_know,
                    date=month
                )

                # Only site surveys have a "location"
                if content_type == 'site':
                    survey.location = location

                survey.save()

                created.append(survey)
            except IntegrityError:
                transaction.rollback()
                date_string = month.strftime("%B, %Y")
                location = cls.location_display(location)
                if content_type == 'site':
                    raise IntegrityError("There is already a survey for {0} for the month {1} and location {2}. Please delete the existing survey first if you're trying to replace it.".format(content_object.name, date_string, location))
                else:
                    raise IntegrityError("There is already a survey for {0} for the month {1}. Please delete the existing survey first if you're trying to replace it.".format(content_object.name, date_string))

        return created

    def __unicode__(self):
        if self.location:
            return "{0} - {1} - {2}".format(self.content_object.name, self.date, self.get_location_display())
        else:
            return "{0} - {1}".format(self.content_object.name, self.date)

    class Meta:
        # We can only have one survey per org/parent, per month, per location
        # IE: you can't survey the A&E ward in one hospital twice in the same
        # month
        unique_together = ('content_type', 'object_id', 'date', 'location')
        ordering = ['-date']


class OrganisationParent(MailSendMixin, AuditedModel):
    """Stores parent bodies of :model:`organisations.Organisation`.

    In the case of Hospitals or Clinics, this is an NHS Trust, in the
    case of GP Branches, this is the main surgery for the branche.
    """
    # Name of the Parent
    name = models.TextField()
    # Unique code for the Parent - called intermittently and ODS code or NACS
    # code by the NHS.
    code = models.CharField(max_length=8, db_index=True, unique=True)
    # The id of the parent on the NHS Choices system. This is explicitly not
    # to be trusted or used unless it absolutely necessary, as they say it
    # may change without warning.
    choices_id = models.IntegerField(db_index=True)
    # The users associated with this parent
    users = models.ManyToManyField(User, related_name='organisation_parents')

    # General email address for this parent. When problems are reported to one
    # of the parent's Organisations, this is the email address we tell about
    # it.
    # max_length set manually to make it RFC compliant (default of 75 is too
    # short) email may not be unique - for example a catch-all address may be
    # used
    email = models.EmailField(max_length=254)
    # A secondary email address. If supplied, we send emails about new
    # problems here too.
    secondary_email = models.EmailField(max_length=254, blank=True)

    # Which CCG this Parent primarily responsible to
    primary_ccg = models.ForeignKey(CCG, blank=False, null=False, related_name='primary_organisation_parents')

    # Which CCGs commission services from this Parent.
    # This means that those CCGs will be able to see all the problems at
    # this parent's organisations.
    ccgs = models.ManyToManyField(CCG, related_name='organisation_parents')

    # Reverse relation to Surveys
    surveys = generic.GenericRelation(FriendsAndFamilySurvey)

    def save(self, *args, **kwargs):
        """Overriden save to ensure email address is set"""
        if not self.email:
            raise ValidationError("email is required")

        super(OrganisationParent, self).save(*args, **kwargs)

    def can_be_accessed_by(self, user):
        """Can a user access this Organisation Parent?"""

        # Deactivated users - NO
        if not user.is_active:
            return False

        # Django superusers - YES
        if user.is_superuser:
            return True

        # NHS Superusers, Moderators - YES
        if user_in_groups(user, [auth.NHS_SUPERUSERS, auth.CASE_HANDLERS]):
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
        return Group.objects.get(pk=auth.ORGANISATION_PARENTS)

    @property
    def problem_set(self):
        """Return the set of problems related to this OrganisationParent.

        This means problems reported to Organisations who have this
        OrganisationParent as their parent.
        """
        return Problem.objects.filter(organisation__in=self.organisations.all())

    def __unicode__(self):
        """Return a string representation of this OrganisationParent"""
        return self.name


@receiver(post_save, sender=OrganisationParent)
def ensure_ccgs_contains_primary_ccg(sender, **kwargs):
    """post_save signal handler to ensure that organisation_parent.primary_ccg
    is always in organisation_parent.ccgs"""
    organisation_parent = kwargs['instance']
    if organisation_parent.primary_ccg and organisation_parent.primary_ccg not in organisation_parent.ccgs.all():
        organisation_parent.ccgs.add(organisation_parent.primary_ccg)


def organisation_image_upload_path(instance, filename):
    """Return a path for an uploaded image of an Organisation to be stored in"""
    return "/".join(
        [
            'organisation_images',
            partitioned_upload_path_and_obfuscated_name(instance, filename)
        ]
    )


class Organisation(AuditedModel, geomodels.Model):
    """Stores an Organisation - a Hospital, GP, Clinic, etc"""

    # Organisation name
    name = models.TextField(db_index=True)
    # What type of organisation this is - hospital, GP, clinic, etc
    organisation_type = models.CharField(max_length=100, choices=settings.ORGANISATION_CHOICES)
    # The id of the parent on the NHS Choices system. This is explicitly not
    # to be trusted or used unless it absolutely necessary, as they say it
    # may change without warning. We store it because sometimes it is
    # necessary to use it when dealing with the NHS Choices API that doesn't
    # always work off the ODS code.
    choices_id = models.IntegerField(db_index=True)
    # The unique code identifying this organisation. This one should never
    # change. Also called NACS code at times.
    ods_code = models.CharField(max_length=12, db_index=True, unique=True)
    # The organisation's address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_line3 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    county = models.CharField(max_length=50, blank=True)
    postcode = models.CharField(max_length=10, blank=True)

    # The organisation's location
    point = geomodels.PointField()

    # Set a custom manager as an instance of GeoManager - so that we can
    # perform geo-spatial queries against Organisation.
    # See: https://docs.djangoproject.com/en/1.4/ref/contrib/gis/model-api/#geomanager
    objects = geomodels.GeoManager()

    # The parent of this organisation
    parent = models.ForeignKey(OrganisationParent, blank=False, null=False, related_name='organisations')

    # Calculated double_metaphone field, for searching by provider name in a
    # "sounds-like" fashion
    name_metaphone = models.TextField(editable=False)

    # Average review rating from "Would you recommend this provider to your
    # friends and family? question asked on NHS Choices"
    average_recommendation_rating = models.FloatField(blank=True, null=True)

    # Image of the organisation
    image = sorlImageField(upload_to=organisation_image_upload_path, validators=[validate_file_extension], blank=True)

    # Reverse relation to Surveys - this helps us get the surveys for an
    # Organisation easily, because querying them directly with an Organisation
    # is a bit clunky
    surveys = generic.GenericRelation(FriendsAndFamilySurvey)

    @property
    def organisation_type_name(self):
        """Return the nice name for organisation_type"""
        for code, label in settings.ORGANISATION_CHOICES:
            if code == self.organisation_type:
                return label

        # should never get here, but best to have a fallback
        return 'Not Known'

    @property
    def open_issues(self):
        """Return the list of open issues for this organisation"""
        return list(self.problem_set.open_problems())

    def has_time_limits(self):
        """Return whether this organisation has time limits.

        Time limits mean that the organisation has an (unspecified) deadline
        for acknowledging and responding to problems, and hence we should
        count how long they take and display that to people.
        """
        if self.organisation_type in ['hospitals', 'clinics']:
            return True
        else:
            return False

    def has_services(self):
        """Return whether this organisation has services.

        GP's do not have services, Hospitals and Clinics do.
        """
        if self.organisation_type in ['hospitals', 'clinics']:
            return True
        else:
            return False

    def can_be_accessed_by(self, user):
        """Can a given user access this Organisation?"""
        # Access is controlled by the Parent
        return self.parent.can_be_accessed_by(user)

    def save(self, *args, **kwargs):
        """Overriden save to calculate double metaphones for name"""
        # dm() expects unicode data, and gets upset with byte strings
        if isinstance(self.name, unicode):
            unicode_name = self.name
        else:
            unicode_name = unicode(self.name, encoding='utf-8', errors='ignore')
        name_metaphones = dm(unicode_name)
        self.name_metaphone = name_metaphones[0]  # Ignoring the alternative for now
        super(Organisation, self).save(*args, **kwargs)

    def __unicode__(self):
        """String representation of this Organisation"""
        return self.name


class Service(AuditedModel):
    """Stores a Service at a particular :model:`organisations.Organisation`"""
    # Name of the service
    name = models.TextField(db_index=True)
    # Code given to the service - this is unique to the organisation, but not
    # unique throughout the country.
    service_code = models.TextField(db_index=True)
    # Which organisation this service is at
    organisation = models.ForeignKey(Organisation, related_name='services')

    @classmethod
    def service_codes(cls):
        """Return a list of service codes currently in the database"""
        cursor = connection.cursor()
        cursor.execute("""SELECT distinct service_code, name
                          FROM organisations_service
                          ORDER BY name""")
        return cursor.fetchall()

    def __unicode__(self):
        """String representation of this Service"""
        return self.name

    class Meta:
        # We should only have one service with a given code at any one
        # Organisation
        unique_together = (("service_code", "organisation"),)


class SuperuserLogEntry(AuditedModel):
    """Stores logs of when an NHS Superuser accesses a page"""
    # The user in question
    user = models.ForeignKey(User, related_name='superuser_access_logs')
    # The page of the page they accessed
    path = models.TextField()
