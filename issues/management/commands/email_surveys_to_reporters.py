from datetime import datetime
import random

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils.timezone import utc
from django.db import transaction
from django.template.loader import get_template
from django.conf import settings
from django.template import Context
from django.core.urlresolvers import reverse


from ...models import Problem
from ...lib import int_to_base32


@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email surveys to problem reporters'

    @classmethod
    def now_utc(cls):
        return datetime.utcnow().replace(tzinfo=utc)

    def handle(self, *args, **options):
        verbosity = self.verbosity = int(options.get('verbosity'))
        surveyable_problems = Problem.objects.requiring_survey_to_be_sent()

        if verbosity >= 2:
            self.stdout.write("{0} surveys to email\n".format(len(surveyable_problems)))

        if len(surveyable_problems) > 0:
            # Get the template
            survey_template = get_template('issues/survey_email.txt')

            # Loop over them and send
            for problem in surveyable_problems:
                try:
                    self.send_survey(survey_template, problem)
                    # reload the problem from db to be sure that the version is fresh
                    problem = Problem.objects.get(pk=problem.id)
                    problem.survey_sent = self.now_utc()
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    if verbosity >= 1:
                        self.stderr.write("{0}\n".format(e))
                        self.stderr.write("Error mailing survey: {0}\n".format(problem.reference_number))
                    transaction.rollback()

    def send_survey(self, template, problem):
        interval = (self.now_utc() - problem.created).days
        survey_params = {'cobrand': problem.cobrand,
                         'token': problem.make_token(random.randint(0,32767)),
                         'id': int_to_base32(problem.id) }
        survey_params['response'] = 'y'
        yes_url = reverse('survey-form', kwargs=survey_params)
        survey_params['response'] = 'n'
        no_url = reverse('survey-form', kwargs=survey_params)
        survey_params['response'] = 'd'
        no_answer_url = reverse('survey-form', kwargs=survey_params)

        # Get the right site base url for the cobrand the problem was raised under
        site_base_url = settings.COBRAND_BASE_URLS.get(problem.cobrand, None)
        if not site_base_url:
            site_base_url = settings.SITE_BASE_URL

        context = Context({
            'problem': problem,
            'interval_in_days': interval,
            'yes_url': yes_url,
            'no_url': no_url,
            'no_answer_url': no_answer_url,
            'site_base_url': site_base_url
        })

        if self.verbosity >= 2:
            self.stdout.write("Emailing survey for problem reference number: {0}\n".format(problem.reference_number))

        mail.send_mail(subject='Care Connect Survey',
                  message=template.render(context),
                  from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=[problem.reporter_email],
                  fail_silently=False)

