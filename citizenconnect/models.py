from django.db import models

class AuditedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class MessageModel(AuditedModel):
    """
    Abstract model for base functionality of messages sent to NHS Organisations
    """

    ORGANISATION_CHOICES = (
        (u'hospitals', u'Hospital'),
        (u'gppractices', u'GP'),
    )
    CONTACT_CHOICES = (
        (u'email', u'By Email'),
        (u'phone', u'By Phone')
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
    organisation_type = models.CharField(max_length=100, choices=ORGANISATION_CHOICES)
    choices_id = models.IntegerField(db_index=True)
    description = models.TextField()
    reporter_name = models.CharField(max_length=200, blank=True)
    reporter_phone = models.CharField(max_length=50, blank=True)
    reporter_email = models.CharField(max_length=254, blank=True)
    public = models.BooleanField()
    public_reporter_name = models.BooleanField()
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default='email')
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)

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