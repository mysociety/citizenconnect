import logging
from datetime import datetime, timedelta

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.timezone import utc
from django.db import transaction
from django.template.loader import get_template
from django.conf import settings
from django.template import Context

from ...models import Problem

logger = logging.getLogger(__name__)

@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email surveys to problem reporters'

    def handle(self, *args, **options):
        now = datetime.utcnow().replace(tzinfo=utc)
        survey_interval = timedelta(days=settings.SURVEY_INTERVAL_IN_DAYS)
        survey_cutoff = now - survey_interval
        surveyable_problems = Problem.objects.filter(Q(survey_sent__isnull=True) &
                                                     Q(created__lte=survey_cutoff) &
                                                     Q(reporter_email__isnull=False))

        logger.info('{0} surveys to email'.format(len(surveyable_problems)))
        if len(surveyable_problems) > 0:
            # Get the template
            survey_template = get_template('issues/survey_email.txt')

            # Loop over them and send
            for problem in surveyable_problems:
                try:
                    self.send_survey(survey_template, problem)
                    problem.survey_sent = datetime.utcnow().replace(tzinfo=utc)
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    logger.error('{0}'.format(e))
                    logger.error('Error mailing survey: {0}'.format(problem.reference_number))
                    transaction.rollback()

    def send_survey(self, template, problem):
        interval = (datetime.utcnow().replace(tzinfo=utc) - problem.created).days
        context = Context({'problem': problem,
                           'interval_in_days': interval})
        logger.info('Emailing survey for problem reference number: {0}'.format(problem.reference_number))

        mail.send_mail(subject='Care Connect Survey',
                  message=template.render(context),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[problem.reporter_email],
                  fail_silently=False)

