from django.db import models

from citizenconnect.models import AuditedModel


class Article(AuditedModel):
    guid = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField()
    author = models.CharField(max_length=50, blank=True)
    published = models.DateTimeField()
