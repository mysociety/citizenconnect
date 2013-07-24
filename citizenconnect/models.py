import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def validate_file_extension(image):
        """ Check that the file extension is within one of the allowed file types """
        extension = os.path.splitext(image.name)[1]
        # settings.ALLOWED_IMAGE_EXTENSIONS should be all lower case variants
        if extension.lower() not in settings.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                u'Sorry, that is not an allowed image type. Allowed image types are: {0}'
                .format(", ".join(settings.ALLOWED_IMAGE_EXTENSIONS))
            )
