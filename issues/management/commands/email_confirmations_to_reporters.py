import logging
from datetime import datetime, timedelta

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from django.db import transaction
from django.template.loader import get_template
from django.conf import settings
from django.template import Context


from ...models import Problem

logger = logging.getLogger(__name__)

@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email confirmations to problem reporters'

    def handle(self, *args, **options):

        problems = Problem.objects.requiring_confirmation()

        logger.info('{0} confirmations to email'.format(len(problems)))

        if len(problems) > 0:

            # Loop over them and send
            for problem in problems:
                try:
                    self.send_confirmation(problem)
                    problem.confirmation_sent = datetime.utcnow().replace(tzinfo=utc)
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    logger.error('{0}'.format(e))
                    logger.error('Error mailing confirmation: {0}'.format(problem.reference_number))
                    transaction.rollback()

    def send_confirmation(self, problem):

        subject_template = get_template('issues/problem_confirmation_email_subject.txt')
        message_template = get_template('issues/problem_confirmation_email_message.txt')

        context = Context({'object': problem,
                           'site_base_url': settings.SITE_BASE_URL,
                           'survey_interval_in_days': settings.SURVEY_INTERVAL_IN_DAYS })

        logger.info('Emailing confirmation for problem reference number: {0}'.format(problem.reference_number))

        mail.send_mail(
            subject=subject_template.render(context),
            message=message_template.render(context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[problem.reporter_email],
            fail_silently=False,
        )

