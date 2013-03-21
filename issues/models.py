from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q

from citizenconnect.models import AuditedModel

class IssueModel(AuditedModel):
    """
    Abstract model for base functionality of issues sent to NHS Organisations
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

    description = models.TextField(verbose_name='')
    reporter_name = models.CharField(max_length=200, blank=False, verbose_name='')
    reporter_phone = models.CharField(max_length=50, blank=True, verbose_name='')
    reporter_email = models.CharField(max_length=254, blank=True, verbose_name='')
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default=CONTACT_EMAIL)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)
    mailed = models.BooleanField(default=False, blank=False)

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
        return super(QuestionManager, self).all().filter(status=Question.NEW)

class Question(IssueModel):
    # Custom manager
    objects = QuestionManager()

    NEW = 0
    RESOLVED = 1

    STATUS_CHOICES = (
        (NEW, 'Open'),
        (RESOLVED, 'Resolved'),
    )

    PREFIX = 'Q'

    category = models.CharField(max_length=100,
                                choices=IssueModel.CATEGORY_CHOICES,
                                default='general',
                                db_index=True,
                                verbose_name='Please select the category that best describes your question')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    postcode = models.CharField(max_length=25, blank=True)
    organisation = models.ForeignKey('organisations.Organisation', blank=True, null=True)
    response = models.TextField(blank=True)

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)

    @property
    def reporter_name_display(self):
        return self.reporter_name

    @property
    def summary(self):
        # TODO - make this a setting?
        summary_length = 30
        if len(self.description) > summary_length:
            return self.description[:summary_length] + '...'
        else:
            return self.description

class ProblemManager(models.Manager):
    use_for_related_fields = True

    def open_problems(self):
        """
        Return only open problems
        """
        return super(ProblemManager, self).all().filter(Q(status__in=Problem.OPEN_STATUSES))

    def unmoderated_problems(self):
        return super(ProblemManager, self).all().filter(moderated=Problem.NOT_MODERATED)

    def open_moderated_published_problems(self):
        return self.open_problems().filter(moderated=Problem.MODERATED,
                                           publication_status=Problem.PUBLISHED)

    def all_moderated_published_problems(self):
        return super(ProblemManager, self).all().filter(moderated=Problem.MODERATED,
                                                        publication_status=Problem.PUBLISHED)

    def problems_requiring_legal_moderation(self):
        return super(ProblemManager, self).all().filter(requires_legal_moderation=True)

    def open_escalated_problems(self):
        # ESCALATION_STATUSES is a subset of OPEN_STATUSES, so
        # we don't need to filter for open too
        return super(ProblemManager, self).all().filter(Q(status__in=Problem.ESCALATION_STATUSES) | Q(breach=True))

class Problem(IssueModel):
    # Custom manager
    objects = ProblemManager()

    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2
    ESCALATED = 3

    STATUS_CHOICES = (
        (NEW, 'Open'),
        (ACKNOWLEDGED, 'In Progress'),
        (RESOLVED, 'Resolved'),
        (ESCALATED, 'Escalated')
    )

    BASE_OPEN_STATUSES = [NEW, ACKNOWLEDGED]
    ESCALATION_STATUSES = [ESCALATED]

    OPEN_STATUSES = BASE_OPEN_STATUSES + ESCALATION_STATUSES

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

    category = models.CharField(max_length=100,
                                choices=IssueModel.CATEGORY_CHOICES,
                                default='other',
                                db_index=True,
                                verbose_name='Please select the category that best describes your problem')
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    organisation = models.ForeignKey('organisations.Organisation')
    service = models.ForeignKey('organisations.Service',
                                null=True,
                                blank=True,
                                verbose_name="Please select a department (optional)")
    happy_service = models.NullBooleanField()
    happy_outcome = models.NullBooleanField()

    # Integer values represent time in minutes
    time_to_acknowledge = models.IntegerField(null=True)
    time_to_address = models.IntegerField(null=True)

    publication_status = models.IntegerField(default=HIDDEN,
                                             blank=False,
                                             choices=PUBLICATION_STATUS_CHOICES)
    moderated = models.IntegerField(default=NOT_MODERATED,
                                    blank=False,
                                    choices=MODERATED_STATUS_CHOICES)
    moderated_description = models.TextField(blank=True)
    breach = models.BooleanField(default=False, blank=False)
    requires_legal_moderation = models.BooleanField(default=False, blank=False)
    commissioned = models.IntegerField(blank=True, null=True, choices=COMMISSIONED_CHOICES)

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.PREFIX, self.id)

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

    def summarise(self, field):
        summary_length = 30
        if len(field) > summary_length:
            return field[:summary_length] + '...'
        else:
            return field

    def can_be_accessed_by(self, user):
        """
        Whether or not an issue is accessible to a given user.
        In practice the issue is publically accessible to everyone if it's public
        and has been moderated to be publically available, otherwise only people
        with access to the organisation it is assigned to can access it.
        """
        return (self.public and self.publication_status == Problem.PUBLISHED) or self.organisation.can_be_accessed_by(user)
