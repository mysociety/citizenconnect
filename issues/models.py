import logging
logger = logging.getLogger(__name__)

from datetime import datetime, timedelta
import hmac
import hashlib

from django.db import models
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db.models import Q
from django.template import Context
from django.template.loader import get_template
from django.utils.timezone import utc

import dirtyfields

from concurrency.fields import IntegerVersionField
from concurrency.api import concurrency_check

from citizenconnect.models import AuditedModel
from .lib import base32_to_int, int_to_base32


class ProblemQuerySet(models.query.QuerySet):

    # The fields to sort by. Used in the tables code.
    ORDER_BY_FIELDS_FOR_MODERATION_TABLE = ('priority', 'created')

    def order_for_moderation_table(self):
        """
        Sort by priority first, then by creation date. This is a crude way to
        ensure that the issues at the top of the moderation list are the ones
        that should be looked at next.

        This sorting could be improved by calculating a deadline for each
        problem and then sorting by that deadline. This would be the ideal as it
        would prevent high priority issues blocking long standing low priority
        ones.
        """
        args = self.ORDER_BY_FIELDS_FOR_MODERATION_TABLE
        return self.order_by(*args)


class ProblemManager(models.Manager):
    use_for_related_fields = True

    # Note: it may be desirable in future to move some of the methods from
    # ProblemManager to ProblemQuerySet.

    def get_query_set(self):
        return ProblemQuerySet(self.model, using=self._db)

    def open_problems(self):
        """
        Return only open problems
        """
        return self.all().filter(Q(status__in=Problem.OPEN_STATUSES))

    def closed_problems(self):
        """
        Return only closed problems
        """
        return self.all().filter(Q(status__in=Problem.CLOSED_STATUSES))

    def unmoderated_problems(self):
        return self.all().filter(moderated=Problem.NOT_MODERATED)

    def open_moderated_published_visible_problems(self):
        return self.open_problems().filter(moderated=Problem.MODERATED,
                                           publication_status=Problem.PUBLISHED,
                                           status__in=Problem.VISIBLE_STATUSES)

    def closed_moderated_published_visible_problems(self):
        return self.closed_problems().filter(moderated=Problem.MODERATED,
                                             publication_status=Problem.PUBLISHED,
                                             status__in=Problem.VISIBLE_STATUSES)

    def all_moderated_published_problems(self):
        return self.all().filter(moderated=Problem.MODERATED,
                                 publication_status=Problem.PUBLISHED,
                                 status__in=Problem.VISIBLE_STATUSES)

    def problems_requiring_second_tier_moderation(self):
        return self.all().filter(requires_second_tier_moderation=True)

    def open_escalated_problems(self):
        return self.all().filter(Q(status__in=Problem.ESCALATION_STATUSES) &
                                 Q(status__in=Problem.OPEN_STATUSES))

    def open_unescalated_problems(self):
        return self.all().filter(Q(status__in=Problem.OPEN_STATUSES) &
                                 Q(status__in=Problem.NON_ESCALATION_STATUSES))


class Problem(dirtyfields.DirtyFieldsMixin, AuditedModel):
    # Custom manager
    objects = ProblemManager()

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2
    ESCALATED = 3
    UNABLE_TO_RESOLVE = 4
    REFERRED_TO_OTHER_PROVIDER = 5
    UNABLE_TO_CONTACT = 6
    ABUSIVE = 7
    ESCALATED_ACKNOWLEDGED = 8
    ESCALATED_RESOLVED = 9
    FORMAL_COMPLAINT = 10

    STATUS_CHOICES = (
        (NEW, 'Open'),
        (ACKNOWLEDGED, 'In Progress'),
        (RESOLVED, 'Responded to'),
        (ESCALATED, 'Escalated'),
        (UNABLE_TO_RESOLVE, 'Unable to Resolve'),
        (REFERRED_TO_OTHER_PROVIDER, 'Referred to Another Provider'),
        (UNABLE_TO_CONTACT, 'Unable to Contact'),
        (ABUSIVE, 'Abusive/Vexatious'),
        (ESCALATED_ACKNOWLEDGED, 'Escalated - In Progress'),
        (ESCALATED_RESOLVED, 'Escalated - Resolved'),
        (FORMAL_COMPLAINT, 'Formal Complaint')
    )

    # The numerical value of the priorities should be chosen so that when sorted
    # ascending higher priorities come first. Please leave gaps in the range so that
    # future priority levels can be added without changing the existing ones.
    PRIORITY_HIGH = 20
    PRIORITY_NORMAL = 50

    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_NORMAL, 'Normal'),
    )

    # Assigning individual statuses to status sets
    BASE_OPEN_STATUSES = [NEW, ACKNOWLEDGED]
    OPEN_ESCALATION_STATUSES = [ESCALATED, ESCALATED_ACKNOWLEDGED]
    HIDDEN_STATUSES = [ABUSIVE]

    # Calculated status sets
    ALL_STATUSES = [status for status, description in STATUS_CHOICES]
    OPEN_STATUSES = BASE_OPEN_STATUSES + OPEN_ESCALATION_STATUSES
    CLOSED_STATUSES = [RESOLVED, UNABLE_TO_RESOLVE, UNABLE_TO_CONTACT, ABUSIVE, ESCALATED_RESOLVED, FORMAL_COMPLAINT]
    ESCALATION_STATUSES = OPEN_ESCALATION_STATUSES + [ESCALATED_RESOLVED]
    NON_ESCALATION_STATUSES = [status for status in ALL_STATUSES if status not in ESCALATION_STATUSES]
    VISIBLE_STATUSES = [status for status in ALL_STATUSES if status not in HIDDEN_STATUSES]
    VISIBLE_STATUS_CHOICES = [(status, description) for status, description in STATUS_CHOICES if status in VISIBLE_STATUSES]

    PREFIX = 'P'

    HIDDEN = 0
    PUBLISHED = 1

    PUBLICATION_STATUS_CHOICES = ((HIDDEN, "Hidden"), (PUBLISHED, "Published"))

    NOT_MODERATED = 0
    MODERATED = 1

    MODERATED_STATUS_CHOICES = ((NOT_MODERATED, "Not moderated"), (MODERATED, "Moderated"))

    LOCALLY_COMMISSIONED = 0
    NATIONALLY_COMMISSIONED = 1

    COMMISSIONED_CHOICES = ((LOCALLY_COMMISSIONED, "Locally Commissioned"),
                            (NATIONALLY_COMMISSIONED, "Nationally Commissioned"))

    CATEGORY_CHOICES = (
        (u'staff', u'Staff Attitude'),
        (u'access', u'Access to Service'),
        (u'delays', u'Delays'),
        (u'treatment', u'Your Treatment'),
        (u'communication', u'Communication'),
        (u'cleanliness', u'Cleanliness'),
        (u'equipment', u'Equipment'),
        (u'medicines', u'Medicines'),
        (u'food', u'Food'),
        (u'dignity', u'Dignity and Privacy'),
        (u'parking', u'Parking'),
        (u'lostproperty', u'Lost Property'),
        (u'other', u'Other'),
    )

    CATEGORY_DESCRIPTIONS = {'staff': 'Bedside manner and attitude of staff',
                             'access': 'Difficulty getting appointments, long waiting times',
                             'delays': 'Delays in care, e.g. referrals and test results',
                             'treatment': 'Wrong advice / unsafe care / refusal of treatment / consent',
                             'communication': 'Communications and administration e.g. letters',
                             'cleanliness': 'Cleanliness and facilities',
                             'equipment': 'Problems with equipment, aids and devices',
                             'medicines': 'Problems with medicines',
                             'food': '',  # TODO Add long description
                             'dignity': 'Privacy, dignity, confidentiality',
                             'parking': 'Problems with parking / charges',
                             'lostproperty': 'Lost property',
                             'other': ''}

    # Not all categories may have elevated priorites set when the issue is
    # reported.
    CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION = (
        'cleanliness',
        'communication',
        'delays',
        'dignity',
        'food',
        'staff',
        'medicines',
        'treatment',
    )

    CONTACT_PHONE = 'phone'
    CONTACT_EMAIL = 'email'

    CONTACT_CHOICES = (
        (CONTACT_EMAIL, u'By Email'),
        (CONTACT_PHONE, u'By Phone')
    )

    # Names for transitions between statuses we might want to print
    TRANSITIONS = {
        'status': {
            'Acknowledged': [[NEW, ACKNOWLEDGED], [ESCALATED, ESCALATED_ACKNOWLEDGED]],
            'Escalated': [[NEW, ESCALATED], [ACKNOWLEDGED, ESCALATED]],
            'Resolved': [[ACKNOWLEDGED, RESOLVED], [ESCALATED_ACKNOWLEDGED, ESCALATED_RESOLVED]]
        },
        'publication_status': {
            'Published': [[HIDDEN, PUBLISHED]],
            'Hidden': [[PUBLISHED, HIDDEN]]
        },
        'moderated': {
            'Moderated': [[NOT_MODERATED, MODERATED]]
        }
    }

    # Which attrs are interesting to compare for revisions
    # The order of these determines the order they are output as a string
    REVISION_ATTRS = ['moderated', 'publication_status', 'status']

    SOURCE_PHONE = 'phone'
    SOURCE_EMAIL = 'email'
    SOURCE_SMS = 'sms'

    SOURCE_CHOICES = (
        (SOURCE_EMAIL, 'Email'),
        (SOURCE_PHONE, 'Phone'),
        (SOURCE_SMS, 'SMS')
    )

    COBRAND_CHOICES = [(cobrand, cobrand) for cobrand in settings.ALLOWED_COBRANDS]

    # We need
    description = models.TextField(verbose_name='', validators=[MaxLengthValidator(2000)])
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)
    reporter_name = models.CharField(max_length=200, blank=False, verbose_name='')
    reporter_phone = models.CharField(max_length=50, blank=True, verbose_name='')
    reporter_email = models.CharField(max_length=254, blank=False, verbose_name='')
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default=CONTACT_EMAIL)
    category = models.CharField(max_length=100,
                                choices=CATEGORY_CHOICES,
                                default='other',
                                db_index=True,
                                verbose_name='Please select the category that best describes your problem')
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    priority = models.IntegerField(default=PRIORITY_NORMAL, choices=PRIORITY_CHOICES)
    organisation = models.ForeignKey('organisations.Organisation')
    service = models.ForeignKey('organisations.Service',
                                null=True,
                                blank=True,
                                verbose_name="Please select a department (optional)")

    happy_service = models.NullBooleanField()
    happy_outcome = models.NullBooleanField()

    # Integer values represent time in minutes
    time_to_acknowledge = models.IntegerField(blank=True, null=True)
    time_to_address = models.IntegerField(blank=True, null=True)
    resolved = models.DateTimeField(blank=True, null=True)

    publication_status = models.IntegerField(default=HIDDEN,
                                             blank=False,
                                             choices=PUBLICATION_STATUS_CHOICES)
    moderated = models.IntegerField(default=NOT_MODERATED,
                                    blank=False,
                                    choices=MODERATED_STATUS_CHOICES)
    moderated_description = models.TextField(blank=True)
    breach = models.BooleanField(default=False, blank=False)
    requires_second_tier_moderation = models.BooleanField(default=False, blank=False)
    commissioned = models.IntegerField(blank=True, null=True, choices=COMMISSIONED_CHOICES)
    survey_sent = models.DateTimeField(null=True, blank=True)
    cobrand = models.CharField(max_length=30, blank=False, choices=COBRAND_CHOICES)
    mailed = models.BooleanField(default=False, blank=False)
    relates_to_previous_problem = models.BooleanField(default=False, blank=False)

    version = IntegerVersionField()

    @models.permalink
    def get_absolute_url(self):
        return ('problem-view', (),  {'pk': self.id, 'cobrand': 'choices'})

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)

    def __unicode__(self):
        return self.reference_number

    @property
    def reporter_name_display(self):
        if self.public_reporter_name:
            return self.reporter_name
        else:
            return "Anonymous"

    @property
    def summary(self):
        if (self.public and self.publication_status == Problem.PUBLISHED):
            return self.summarise(self.moderated_description)
        else:
            return "Private"

    @property
    def private_summary(self):
        return self.summarise(self.description)

    @property
    def has_elevated_priority(self):
        return self.priority < Problem.PRIORITY_NORMAL

    def clean(self):
        """
        Custom model validation
        """
        super(Problem, self).clean()
        # Check that if they prefer to be contacted by phone, they actually provided a number
        if self.preferred_contact_method == self.CONTACT_PHONE and not self.reporter_phone:
            raise ValidationError('You must provide a phone number if you prefer to be contacted by phone')

    def summarise(self, field):
        summary_length = 30
        if len(field) > summary_length:
            return field[:summary_length] + '...'
        else:
            return field

    def can_be_accessed_by(self, user):
        """
        Whether or not an issue is accessible to a given user.
        In practice the issue is publically accessible to everyone if it's public,
        in a visible status and has been moderated to be publically available,
        otherwise only people with access to the organisation it is assigned to can access it.
        """
        return (self.public
                and self.publication_status == Problem.PUBLISHED and
                int(self.status) in Problem.VISIBLE_STATUSES) \
                or self.organisation.can_be_accessed_by(user)

    def set_time_to_values(self):
        """
        Set the time_to_address, time_to_acknowledge and resolved
        times
        """
        now = datetime.utcnow().replace(tzinfo=utc)
        minutes_since_created = self.timedelta_to_minutes(now - self.created)
        statuses_which_indicate_acknowledgement = [Problem.ACKNOWLEDGED,
                                                   Problem.RESOLVED,
                                                   Problem.ESCALATED_ACKNOWLEDGED,
                                                   Problem.ESCALATED_RESOLVED]
        statuses_which_indicate_resolution = [Problem.RESOLVED,
                                              Problem.ESCALATED_RESOLVED]
        if self.time_to_acknowledge is None and int(self.status) in statuses_which_indicate_acknowledgement:
            self.time_to_acknowledge = minutes_since_created
        if self.time_to_address is None and int(self.status) in statuses_which_indicate_resolution:
            self.time_to_address = minutes_since_created
            self.resolved = now

    def save(self, *args, **kwargs):
        """Override the default model save() method in order to populate time_to_acknowledge
        or time_to_address if appropriate."""
        concurrency_check(self, *args, **kwargs)  # Do a concurrency check

        if self.created:
            self.set_time_to_values()

        # capture the old state of the problem to use after the actual save has
        # run. If there is no value it has not been changed since the last save,
        # so use the current value. Or use None if this is a new entry.
        if self.pk:
            previous_status_value = self.get_dirty_fields().get('status', self.status)
        else:
            previous_status_value = None

        super(Problem, self).save(*args, **kwargs)  # Call the "real" save() method.

        # This should be run by the post-save signal, but it does not seem to
        # run. Adding it here manually to get it working. See https://github.com/smn/django-dirtyfields/blob/master/src/dirtyfields/dirtyfields.py
        # for the code that should run. This is why django-dirtyfields is pinned to 0.1
        #
        # Slightly changed contents of dirtyfields.reset_state:
        self._original_state = self._as_dict()

        # If we are now ESCALATED, but were not before the save, send email
        if self.status == self.ESCALATED and previous_status_value != self.ESCALATED:
            self.send_escalation_email()

    def check_token(self, token):
        try:
            rand, hash = token.split("-")
        except:
            return False

        try:
            rand = base32_to_int(rand)
        except:
            return False

        if self.make_token(rand) != token:
            return False
        return True

    def make_token(self, rand):
        rand = int_to_base32(rand)
        hash = hmac.new(settings.SECRET_KEY, unicode(self.id) + rand, hashlib.sha1).hexdigest()[::2]
        return "%s-%s" % (rand, hash)

    @classmethod
    def timedelta_to_minutes(cls, timedelta):
        days_in_minutes = timedelta.days * 60 * 24
        seconds_in_minutes = timedelta.seconds / 60
        return days_in_minutes + seconds_in_minutes

    def send_escalation_email(self):
        """
        Send the escalation email. Throws exception if status is not 'ESCALATED'.
        """

        # Safety check to prevent accidentally sending emails when not appropriate
        if self.status != self.ESCALATED:
            raise ValueError("Problem status of '{0}' is not 'ESCALATED'".format(self))

        # gather the templates and create the context for them
        subject_template = get_template('issues/escalation_email_subject.txt')
        message_template = get_template('issues/escalation_email_message.txt')

        context = Context({
            'object':        self,
            'site_base_url': settings.SITE_BASE_URL
        })

        logger.info('Sending escalation email for {0}'.format(self))

        kwargs = dict(
            subject=subject_template.render(context),
            message=message_template.render(context),
        )

        if self.commissioned == self.LOCALLY_COMMISSIONED:
            # Send email to the CCG
            self.organisation.escalation_ccg.send_mail(**kwargs)
        elif self.commissioned == self.NATIONALLY_COMMISSIONED:
            # send email to CCC
            mail.send_mail(
                recipient_list=settings.CUSTOMER_CONTACT_CENTRE_EMAIL_ADDRESSES,
                from_email=settings.DEFAULT_FROM_EMAIL,
                **kwargs
            )
        else:
            raise ValueError("commissioned must be set to select destination for escalation email for {0}".format(self))
