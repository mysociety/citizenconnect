from django.db import models

from citizenconnect.models import AuditedModel
from issues.models import Problem, Question

class MessageResponse(AuditedModel):
    """
    A response to a message
    """
    response = models.TextField()

    class Meta:
        abstract = True

class ProblemResponse(MessageResponse):
    message = models.ForeignKey(Problem, related_name='responses')

class QuestionResponse(MessageResponse):
    message = models.ForeignKey(Question, related_name='responses')
