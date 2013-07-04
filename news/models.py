from django.db import models

from citizenconnect.models import AuditedModel


class Article(AuditedModel):
    title = models.CharField(blank=False)
    description = models.TextField()
    published = models.DateTimeField()
