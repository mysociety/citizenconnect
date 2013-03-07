from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q

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

    CATEGORY_CHOICES = (
        (u'staff', u'Staff Attitude'),
        (u'access', u'Access to Service'),
        (u'delays', u'Delays'),
        (u'treatment', u'Your Treatment'),
        (u'communication', u'Communication'),
        (u'cleanliness', u'Cleanliness'),
        (u'equipment', u'Equipment'),
        (u'medicines', u'Medicines'),
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
                             'dignity': 'Privacy, dignity, confidentiality',
                             'parking': 'Problems with parking / charges',
                             'lostproperty': 'Lost property',
                             'other': ''}

    HIDDEN = 0
    PUBLISHED = 1

    PUBLICATION_STATUS_CHOICES = ((HIDDEN, "Hidden"), (PUBLISHED, "Published"))

    NOT_MODERATED = 0
    MODERATED = 1

    MODERATED_STATUS_CHOICES = ((NOT_MODERATED, "Not moderated"), (MODERATED, "Moderated"))

    description = models.TextField(verbose_name='')
    reporter_name = models.CharField(max_length=200, blank=True, verbose_name='')
    reporter_phone = models.CharField(max_length=50, blank=True, verbose_name='')
    reporter_email = models.CharField(max_length=254, blank=True, verbose_name='')
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default=CONTACT_EMAIL)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)
    mailed = models.BooleanField(default=False, blank=False)
    publication_status = models.IntegerField(default=HIDDEN, blank=False, choices=PUBLICATION_STATUS_CHOICES)
    moderated = models.IntegerField(default=NOT_MODERATED, blank=False, choices=MODERATED_STATUS_CHOICES)

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
        return super(QuestionManager, self).all().filter(Q(status=Question.NEW) | Q(status=Question.ACKNOWLEDGED))

    def open_moderated_questions(self):
        return self.open_questions().filter(moderated=MessageModel.MODERATED)

    def open_unmoderated_questions(self):
        return self.open_questions().filter(moderated=MessageModel.NOT_MODERATED)

    def open_moderated_published_questions(self):
        return self.open_moderated_questions().filter(publication_status=MessageModel.PUBLISHED)

    def open_moderated_published_public_questions(self):
        return self.open_moderated_published_questions().filter(public=True)

class Question(MessageModel):
    # Custom manager
    objects = QuestionManager()

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2

    STATUS_CHOICES = (
        (NEW, 'Received but not acknowledged'),
        (ACKNOWLEDGED, 'Acknowledged but not answered'),
        (RESOLVED, 'Question answered'),
    )

    PREFIX = 'Q'

    category = models.CharField(max_length=100,
                                choices=MessageModel.CATEGORY_CHOICES,
                                default='general',
                                db_index=True,
                                verbose_name='Please select the category that best describes your question')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    postcode = models.CharField(max_length=25, blank=True)

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
    def open_moderated_problems(self):
        return self.open_problems().filter(moderated=MessageModel.MODERATED)

    def open_unmoderated_problems(self):
        return self.open_problems().filter(moderated=MessageModel.NOT_MODERATED)

    def open_moderated_published_problems(self):
        return self.open_moderated_problems().filter(publication_status=MessageModel.PUBLISHED)

    def open_moderated_published_public_problems(self):
        return self.open_moderated_published_problems().filter(public=True)

class Problem(MessageModel):
    # Custom manager
    objects = ProblemManager()

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

    category = models.CharField(max_length=100,
                                choices=MessageModel.CATEGORY_CHOICES,
                                default='other',
                                db_index=True,
                                verbose_name='Please select the category that best describes your problem')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    organisation = models.ForeignKey('organisations.Organisation')
    service = models.ForeignKey('organisations.Service', null=True, blank=True, verbose_name="Please select a department (optional)")
    happy_service = models.NullBooleanField()
    happy_outcome = models.NullBooleanField()
    time_to_acknowledge = models.IntegerField(null=True)
    time_to_address = models.IntegerField(null=True)

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)
