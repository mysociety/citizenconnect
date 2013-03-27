from datetime import datetime, timedelta

from django.test import TestCase
from django.core.management import call_command
from django.core import mail
from django.utils.timezone import utc
from django.conf import settings

from organisations.tests.lib import create_test_organisation, create_test_service, create_test_instance
from ..models import Problem

class EmailSurveysToReportersTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.test_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                           'service': self.test_service,
                                                           'cobrand': 'choices',
                                                           'reporter_name': 'Problem reporter',
                                                           'reporter_email': 'problem@example.com',
                                                           'reporter_phone': '123456789'})

        self.set_problem_age()

    def set_problem_age(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        self.test_problem_age = settings.SURVEY_INTERVAL_IN_DAYS+1
        interval = timedelta(days=self.test_problem_age)
        Problem.objects.filter(pk=self.test_problem.id).update(created=now-interval)

    def _call_command(self):
        args = []
        opts = {}
        call_command('email_surveys_to_reporters', *args, **opts)

    def test_happy_path(self):
        self._call_command()
        self.assertEqual(len(mail.outbox), 1)
        first_mail = mail.outbox[0]
        self.assertEqual(first_mail.subject, 'Care Connect Survey')
        self.assertEqual(first_mail.from_email, 'no-reply@citizenconnect.mysociety.org')
        self.assertEqual(first_mail.to, ['problem@example.com'])
        self.assertTrue("Dear %s," % self.test_problem.reporter_name in first_mail.body)
        self.assertTrue("%d days ago," % self.test_problem_age in first_mail.body)
        self.assertTrue('/choices/' in first_mail.body)

    def test_sends_no_emails_when_none_to_send(self):
        self.test_problem.survey_sent = datetime.utcnow().replace(tzinfo=utc)
        self.test_problem.save()
        self._call_command()
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_links_using_correct_cobrand(self):
        self.test_problem.cobrand = 'myhealthlondon'
        self.test_problem.save()
        self.set_problem_age()
        self._call_command()
        self.assertEqual(len(mail.outbox), 1)
        first_mail = mail.outbox[0]
        self.assertTrue('/myhealthlondon/' in first_mail.body)
