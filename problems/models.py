from django.db import models
from django.db.models import Q
from django.conf import settings

from citizenconnect.models import MessageModel

class ProblemManager(models.Manager):
    use_for_related_fields = True

    def open_problems(self):
        """
        Return only open problems
        """
        return super(ProblemManager, self).all().filter(Q(status=Problem.NEW) | Q(status=Problem.ACKNOWLEDGED))

class Problem(MessageModel):
    # Custom manager
    objects = ProblemManager()

    CATEGORY_CHOICES = (
        (u'cleanliness', u'Cleanliness'),
        (u'staff', u'Staff'),
        (u'appointments', u'Appointments'),
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

    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES)

    @property
    def prefix(self):
        return 'P'

    @property
    def reference_number(self):
        return '{0}{1}'.format(self.prefix, self.id)