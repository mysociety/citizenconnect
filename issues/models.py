from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError

from citizenconnect.models import AuditedModel

class MessageModel(AuditedModel):
    """
    Abstract model for base functionality of messages sent to NHS Organisations
    """

    CONTACT_PHONE = 'phone'
    CONTACT_EMAIL = 'email'

    CONTACT_CHOICES = (
        (CONTACT_EMAIL, u'By Email'),
        (CONTACT_PHONE, u'By Phone')
    )

    SOURCE_PHONE = 'phone'
    SOURCE_EMAIL = 'email'
    SOURCE_SMS = 'sms'

    SOURCE_CHOICES = (
        (SOURCE_EMAIL, 'Email'),
        (SOURCE_PHONE, 'Phone'),
        (SOURCE_SMS, 'SMS')
    )

    organisation = models.ForeignKey('organisations.Organisation')
    service = models.ForeignKey('organisations.Service', null=True, blank=True, verbose_name="Please select a department (optional)")
    description = models.TextField(verbose_name='')
    reporter_name = models.CharField(max_length=200, blank=True, verbose_name='')
    reporter_phone = models.CharField(max_length=50, blank=True, verbose_name='')
    reporter_email = models.CharField(max_length=254, blank=True, verbose_name='')
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default=CONTACT_EMAIL)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)

    @property
    def summary(self):
        # TODO - make this a setting?
        summary_length = 30
        if len(self.description) > summary_length:
            return self.description[:summary_length] + '...'
        else:
            return self.description

    @property
    def issue_type(self):
        """
        Return the class name, so that it can be printed
        """
        # TODO - this could be a custom template filter instead of a model property
        return self.__class__.__name__

    def clean(self):
        """
        Custom model validation
        """

        # Check that one of phone or email is provided
        if not self.reporter_phone and not self.reporter_email:
            raise ValidationError('You must provide either a phone number or an email address')

        # Check that whichever prefered_contact_method is chosen, they actually provided it
        if self.preferred_contact_method == self.CONTACT_EMAIL and not self.reporter_email:
            raise ValidationError('You must provide an email address if you prefer to be contacted by email')
        elif self.preferred_contact_method == self.CONTACT_PHONE and not self.reporter_phone:
            raise ValidationError('You must provide a phone number if you prefer to be contacted by phone')


    class Meta:
        abstract = True

class QuestionManager(models.Manager):
    use_for_related_fields = True

    def open_questions(self):
        """
        Return only open problems
        """
        return super(QuestionManager, self).all().filter(Q(status=Question.NEW) | Q(status=Question.ACKNOWLEDGED))

class OpenQuestionManager(models.Manager):

    def get_query_set(self):
        return super(OpenQuestionManager, self).get_query_set().filter(Q(status=Question.NEW) | Q(status=Question.ACKNOWLEDGED))

class Question(MessageModel):
    # Custom manager
    objects = QuestionManager()
    open_objects = OpenQuestionManager()

    CATEGORY_CHOICES = (
        (u'services', u'Services'),
        (u'prescriptions', u'Prescriptions'),
        (u'general', u'General'),
    )

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2

    STATUS_CHOICES = (
        (NEW, 'Received but not acknowledged'),
        (ACKNOWLEDGED, 'Acknowledged but not answered'),
        (RESOLVED, 'Question answered'),
    )

    PREFIX = 'Q'

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='general', verbose_name='Please select the category that best describes your problem')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)

class ProblemManager(models.Manager):
    use_for_related_fields = True

    def open_problems(self):
        """
        Return only open problems
        """
        return super(ProblemManager, self).all().filter(Q(status=Problem.NEW) | Q(status=Problem.ACKNOWLEDGED))

class OpenProblemManager(models.Manager):

    def get_query_set(self):
        return super(OpenProblemManager, self).get_query_set().filter(Q(status=Problem.NEW) | Q(status=Problem.ACKNOWLEDGED))

class Problem(MessageModel):
    # Custom managers
    objects = ProblemManager()
    open_objects = OpenProblemManager()

    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
        (u'other', u'Other'),
    )

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2
    NOT_RESOLVED = 3

    STATUS_CHOICES = (
        (NEW, 'Received but not acknowledged'),
        (ACKNOWLEDGED, 'Acknowledged but not addressed'),
        (RESOLVED, 'Addressed - problem solved'),
        (NOT_RESOLVED, 'Addressed - unable to solve')
    )

    PREFIX = 'P'

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='other', verbose_name='Please select the category that best describes your problem')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)
