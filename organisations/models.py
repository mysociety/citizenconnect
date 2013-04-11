import datetime
import logging
logger = logging.getLogger(__name__)

from django.contrib.gis.db import models as geomodels
from django.conf import settings
from django.core import mail
from django.db import models
from django.db.models import Q
from django.db import connection
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from django.template import Context

from citizenconnect.models import AuditedModel

import auth
from .auth import user_in_group, user_in_groups, user_is_superuser, create_unique_username

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

    # Initially empty - this gets a value when the the intro email is sent to the
    # organisation. It doubles up as a flag to say whether the email has been sent or
    # not.
    intro_email_sent = models.DateTimeField(blank=True, null=True, editable=False)

    users = models.ManyToManyField(User, related_name='organisations')

    point =  geomodels.PointField()
    objects = geomodels.GeoManager()
    ccg = models.ForeignKey(CCG, blank=True, null=True)

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
        if self.ccg and user in self.ccg.users.all():
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
    
    
    def send_mail(self, subject, message, fail_silently=False):
        """
        This is very similar to the built in Django function `send_mail` (https://docs.djangoproject.com/en/dev/topics/email/#send-mail)

        It takes the following arguments which are passed through to mail.send_mail:

            subject, message, fail_silently=False
        
        It will auto fill the following arguments:
        
            from_email     - set from settings.DEFAULT_FROM_EMAIL
            recipient_list - set from the organisations details
        
        In addition it will:

          * raise an exception if there are no email addresses for the org - ISSUE-329
          * will create a user account linked to the provider if required
          * will send out an intro email if one has not already been sent
          * will send the email
        """

        kwargs = dict(
            subject        = subject,
            message        = message,
            fail_silently  = fail_silently,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = filter(bool, [self.email]),
        )

        if not len(kwargs['recipient_list']):
            raise ValueError("Organisation '{0}' has no email addresses".format(self))

        self.ensure_related_user_exists()
        
        if not self.intro_email_sent:
            self.send_intro_email()

        return mail.send_mail(**kwargs)


    def send_intro_email(self):
        """
        Send the intro email and put the current time into intro_email_sent field.
        """

        subject_template = get_template('organisations/intro_email_subject.txt')
        message_template = get_template('organisations/intro_email_message.txt')

        context = Context({
            'user': self.users.all()[0],
            'site_base_url': settings.SITE_BASE_URL
        })

        logger.info('Sending intro email to {0}'.format(self))

        kwargs = dict(
            subject        = subject_template.render(context),
            message        = message_template.render(context),
            fail_silently  = False,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = filter(bool, [self.email]),
        )

        if not len(kwargs['recipient_list']):
            raise ValueError("Organisation '{0}' has no email addresses".format(self))

        mail.send_mail(**kwargs)

        self.intro_email_sent = datetime.datetime.now()
        
        return



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
