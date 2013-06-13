import datetime
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core import mail
from django.db import models
from django.template import Context
from django.template.loader import get_template
from django.utils.timezone import utc

from django.contrib.auth.models import User

import auth


class MailSendMixin(models.Model):

    class Meta:
        abstract = True

    # Initially empty - this gets a value when the the intro email is sent to the
    # organisation. It doubles up as a flag to say whether the email has been sent or
    # not.
    intro_email_sent = models.DateTimeField(blank=True, null=True, editable=False)

    def send_mail(self, subject, message, fail_silently=False):
        """
        This is very similar to the built in Django function `send_mail` (https://docs.djangoproject.com/en/dev/topics/email/#send-mail)

        It takes the following arguments which are passed through to mail.send_mail:

            subject, message, fail_silently=False

        It will auto fill the following arguments:

            from_email     - set from settings.DEFAULT_FROM_EMAIL
            recipient_list - set from the organisations details

        In addition it will:

          * raise an exception if there are no email addresses for the org - ISSUE-329
          * will create a user account linked to the provider if required
          * will send out an intro email if one has not already been sent
          * will send the email
        """

        class_name = self.__class__.__name__

        # We can't send email if we don't have an email address
        if not self.email:  # ISSUE-329
            raise ValueError("{0} {1} needs an email to find/create related user".format(class_name, self.id))

        # Organisations send emails to two email addresses
        recipient_list = [self.email]
        if hasattr(self, 'secondary_email'):
            recipient_list.append(self.secondary_email)

        kwargs = dict(
            subject=subject,
            message=message,
            fail_silently=fail_silently,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=filter(bool, recipient_list),
        )

        if not len(kwargs['recipient_list']):
            raise ValueError("'{0}' has no email addresses".format(self))

        return mail.send_mail(**kwargs)
