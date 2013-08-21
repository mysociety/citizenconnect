from django.db import models

from concurrency.api import concurrency_check
from concurrency.fields import IntegerVersionField

from citizenconnect.models import AuditedModel
from issues.models import Problem


class ProblemResponse(AuditedModel):
    """Stores responses to :model:`issues.Problem`."""
    # The response text
    response = models.TextField()
    # The problem this response is for
    issue = models.ForeignKey(Problem, related_name='responses')
    # The version of this response, used by django-concurrency to stop
    # concurrent editing of the response by two different people
    version = IntegerVersionField()

    def save(self, *args, **kwargs):
        """Override the default model save() method in order to do a
        concurrency check."""
        concurrency_check(self, *args, **kwargs) # Do a concurrency check
        super(ProblemResponse, self).save(*args, **kwargs) # Call the "real" save() method.
