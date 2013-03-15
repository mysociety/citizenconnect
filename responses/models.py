from django.db import models

from citizenconnect.models import AuditedModel
from issues.models import Problem

class ProblemResponse(AuditedModel):
    response = models.TextField()
    message = models.ForeignKey(Problem, related_name='responses')
