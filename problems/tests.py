import uuid

from django.test import TestCase

from .models import Problem
from .forms import ProblemForm

class ProblemTests(TestCase):

    def setUp(self):
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.test_problem = {
            'organisation_type': 'gppractices',
            'choices_id': 12702,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': ProblemForm.PRIVACY_PRIVATE,
            'preferred_contact_method': 'phone'
        }

    def test_problem_form_exists(self):
        resp = self.client.get('/choices/problem/problem-form/gppractices/12702')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Report your problem' in resp.content)

    def test_problem_form_happy_path(self):
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        self.assertRedirects(resp, '/choices/problem/problem-confirm')
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.organisation_type, 'gppractices')
        self.assertEqual(problem.choices_id, 12702)
        self.assertEqual(problem.public, False)
        self.assertEqual(problem.public_reporter_name, False)
        self.assertEqual(problem.description, 'This is a problem')
        self.assertEqual(problem.reporter_name, self.uuid)
        self.assertEqual(problem.reporter_email, 'steve@mysociety.org')
        self.assertEqual(problem.preferred_contact_method, 'phone')

    def test_problem_form_respects_name_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PRIVATE_NAME
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, False)

    def test_problem_form_respects_public_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PUBLIC
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, True)

    def test_problem_form_errors_without_email_or_phone(self):
        del self.test_problem['reporter_email']
        del self.test_problem['reporter_phone']
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        self.assertFormError(resp, 'form', None, 'You must provide either a phone number or an email address')

    def test_problem_form_accepts_phone_only(self):
        del self.test_problem['reporter_email']
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        self.assertRedirects(resp, '/choices/problem/problem-confirm')
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)

    def test_problem_form_accepts_email_only(self):
        del self.test_problem['reporter_phone']
        resp = self.client.post('/choices/problem/problem-form/gppractices/12702', self.test_problem)
        self.assertRedirects(resp, '/choices/problem/problem-confirm')
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)