import os
from uuid import uuid4
import random

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditedModel(models.Model):
    """Abstract model class providing datetime fields useful for auditing.

    Provides created and modified datetime fields, which automatically get set
    to the current time on creation, and whenever the model is modified.
    """
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


def partitioned_upload_path_and_obfuscated_name(instance, filename):
    """
    Generate a path and filename which is partitioned between some
    random directories and has an obfuscated name.
    """
    # organisation_images/\w{2}/\w{2}
    letters = 'abcdefghijklmnopqrstuvwxyz'
    random_filename = uuid4().hex
    extension = os.path.splitext(filename)[1]
    return "/".join([
        "".join(random.sample(letters, 2)),
        "".join(random.sample(letters, 2)),
        random_filename + extension
    ])
