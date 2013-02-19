from django.db import models

from citizenconnect.models import AuditedModel

class Response(AuditedModel):
    """
    A response to a message
    """
    response = models.TextField()
