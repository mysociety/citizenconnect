from django.db import models
from django.conf import settings

from citizenconnect.models import AuditedModel

class Problem(AuditedModel):
    ORGANISATION_CHOICES = (
        (u'hospitals', u'Hospital'),
        (u'gppractices', u'GP'),
    )
    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
    )
    CONTACT_CHOICES = (
        (u'email', u'By Email'),
        (u'phone', u'By Phone')
    )
    organisation_type = models.CharField(max_length=100, choices=ORGANISATION_CHOICES)
    choices_id = models.IntegerField(db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    reporter_name = models.CharField(max_length=200, blank=True)
    reporter_phone = models.CharField(max_length=50, blank=True)
    reporter_email = models.CharField(max_length=254, blank=True)
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default='email')

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
        Return the class name, eg: Problem, so that it can be printed
        """
        # TODO - this could be a custom template filter instead of a model property
        return self.__class__.__name__
