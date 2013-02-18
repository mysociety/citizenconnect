
from django.db import models
from django.conf import settings

from organisations import choices_api

class AuditedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

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
    response = models.TextField(blank=True)
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

    class Meta:
        abstract = True
