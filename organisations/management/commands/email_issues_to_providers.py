import logging

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

from issues.models import Question, Problem

logger = logging.getLogger(__name__)

@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email new issues to providers'

    def handle(self, *args, **options):
        new_questions = Question.objects.all().filter(mailed=False)
        new_problems = Problem.objects.all().filter(mailed=False)

        new_issues = list(new_problems) + list(new_questions)

        logger.info('{0} New issues to email'.format(len(new_issues)))

        if len(new_issues) > 0:
            # Get the template
            message_template = get_template('organisations/new_message_email.txt')
            # Loop over them and send
            for issue in new_issues:
                try:
                    self.send_message(message_template, issue)
                    issue.mailed = True
                    issue.save()
                    transaction.commit()
                except Exception as e:
                    logger.error('{0}'.format(e))
                    logger.error('Error mailing message: {0}'.format(issue.reference_number))
                    transaction.rollback()

    def send_message(self, template, issue):
        context = Context({ 'message': issue, 'site_base_url': settings.SITE_BASE_URL })
        logger.info('Emailing message reference number: {0}'.format(issue.reference_number))
        if issue.issue_type == "Problem":
            # TODO - recipient list should come from the organisation
            recipient_list = ['recipient@example.com']
        else:
            recipient_list = [settings.QUESTION_ANSWERERS_EMAIL]

        mail.send_mail(subject='Care Connect: New {0}'.format(issue.issue_type),
                  message=template.render(context),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=recipient_list,
                  fail_silently=False)

