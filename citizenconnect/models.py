import os
import logging
from uuid import uuid4
import random

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

logger = logging.getLogger(__name__)


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

def delete_uploaded_file(storage, path, name, delete_empty_directory=False):
    """
    Delete an uploaded file, and optionally the directory it sits in too if
    it's left empty by the deletion.
    """
    try:
        storage.delete(name)
        if delete_empty_directory:
            directory = os.path.dirname(path)
            empty_directory = ([], [])
            if storage.listdir(directory) == empty_directory:
                # This assumes that we're using the FileSystemStorage class
                # and so can use normal os methods.
                # The Storage API doesn't include a method for
                # deleting directories unfortunately, so we can't abstract it
                # away (and delete doesn't work for directories).
                os.rmdir(directory)
    except NotImplementedError:
        # Some storage classes don't implement the whole Storage API, so we
        # just have to ignore it. Log in case someone's changed the storage
        # and didn't realise.
        logger.exception("Storage raised NotImplementedError whilst cleaning up image: %s", path)
    except Exception:
        # Something else bad happened, we should probably look at this.
        logger.exception("Error whilst cleaning up image: %s", path)
