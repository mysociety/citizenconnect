from datetime import datetime, timedelta

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import utc
from django.db import transaction
from django.template.loader import get_template
from django.conf import settings
from django.template import Context


from ...models import Problem


@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email confirmations to problem reporters'

    def handle(self, *args, **options):
        verbosity = self.verbosity = int(options.get('verbosity'))

        problems = Problem.objects.requiring_confirmation()

        if verbosity >= 2:
            self.stdout.write("{0} confirmations to email\n".format(len(problems)))

        if len(problems) > 0:

            # Loop over them and send
            for problem in problems:
                try:
                    self.send_confirmation(problem)
                    # reload the problem from db to be sure that the version is fresh
                    problem = Problem.objects.get(pk=problem.id)
                    problem.confirmation_sent = datetime.utcnow().replace(tzinfo=utc)
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    if verbosity >= 1:
                        self.stderr.write("{0}\n".format(e))
                        self.stderr.write("Error mailing confirmation: {0}\n".format(problem.reference_number))
                    transaction.rollback()

    def send_confirmation(self, problem):

        subject_template = get_template('issues/problem_confirmation_email_subject.txt')
        message_template = get_template('issues/problem_confirmation_email_message.txt')

        context = Context({'object': problem,
                           'site_base_url': settings.SITE_BASE_URL,
                           'survey_interval_in_days': settings.SURVEY_INTERVAL_IN_DAYS })

        if self.verbosity >= 2:
            self.stdout.write("Emailing confirmation for problem reference number: {0}\n".format(problem.reference_number))

        mail.send_mail(
            subject=subject_template.render(context),
            message=message_template.render(context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[problem.reporter_email],
            fail_silently=False,
        )

