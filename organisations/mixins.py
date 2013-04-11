import datetime
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core import mail
from django.db import models
from django.template import Context
from django.template.loader import get_template
from django.utils.timezone import utc


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

        kwargs = dict(
            subject        = subject,
            message        = message,
            fail_silently  = fail_silently,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = filter(bool, [self.email]),
        )

        if not len(kwargs['recipient_list']):
            raise ValueError("'{0}' has no email addresses".format(self))

        self.ensure_related_user_exists()
        
        if not self.intro_email_sent:
            self.send_intro_email()

        return mail.send_mail(**kwargs)
    

    def send_intro_email(self):
        """
        Send the intro email and put the current time into intro_email_sent field.
        """
    
        subject_template = get_template('organisations/intro_email_subject.txt')
        message_template = get_template('organisations/intro_email_message.txt')
    
        context = Context({
            'user': self.users.all()[0],
            'site_base_url': settings.SITE_BASE_URL
        })
    
        logger.info('Sending intro email to {0}'.format(self))
    
        kwargs = dict(
            subject        = subject_template.render(context),
            message        = message_template.render(context),
            fail_silently  = False,
            from_email     = settings.DEFAULT_FROM_EMAIL,
            recipient_list = filter(bool, [self.email]),
        )
    
        if not len(kwargs['recipient_list']):
            raise ValueError("'{0}' has no email addresses".format(self))
    
        mail.send_mail(**kwargs)
    
        self.intro_email_sent = datetime.datetime.utcnow().replace(tzinfo=utc)
        self.save()
    
        return
