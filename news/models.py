from django.db import models

from sorl.thumbnail import ImageField as sorlImageField

from citizenconnect.models import (
    AuditedModel,
    validate_file_extension,
    partitioned_upload_path_and_obfuscated_name
)

class Article(AuditedModel):
    """Stores news articles"""

    # Globally unique ID
    guid = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    # A short plain text summary of the article content
    description = models.TextField()
    # Full HTML content of the Article
    content = models.TextField()
    # Name of who wrote the article
    author = models.CharField(max_length=50, blank=True)
    # When the Article was published
    published = models.DateTimeField(db_index=True)
    # An image to display alongside this Article
    image = sorlImageField(
        upload_to='article_images',
        validators=[validate_file_extension],
        blank=True
    )
