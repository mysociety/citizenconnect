from django.db import models

from citizenconnect.models import AuditedModel


class Article(AuditedModel):
    title = models.CharField(max_length=255, blank=False)
    description = models.TextField()
    published = models.DateTimeField()
