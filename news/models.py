from django.db import models

from sorl.thumbnail import ImageField as sorlImageField

from citizenconnect.models import (
    AuditedModel,
    validate_file_extension,
    partitioned_upload_path_and_obfuscated_name
)


def article_image_upload_path(instance, filename):
    return "/".join(
        [
            'article_images',
            partitioned_upload_path_and_obfuscated_name(instance, filename)
        ]
    )


class Article(AuditedModel):
    guid = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField()
    author = models.CharField(max_length=50, blank=True)
    published = models.DateTimeField(db_index=True)
    image = sorlImageField(
        upload_to=article_image_upload_path,
        validators=[validate_file_extension],
        blank=True
    )
