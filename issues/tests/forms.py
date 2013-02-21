import uuid

from django.test import TestCase

from organisations.tests.lib import create_test_organisation, create_test_service

from ..models import Problem, Question
from ..forms import ProblemForm, QuestionForm

class ProblemCreateFormTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.other_organisation = create_test_organisation({'ods_code': '22222'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.other_service = create_test_service({'organisation': self.other_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = '/choices/problem/problem-form/%s' % self.test_organisation.ods_code
        self.test_problem = {
            'organisation': self.test_organisation.id,
            'service': self.test_service.id,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': ProblemForm.PRIVACY_PRIVATE,
            'preferred_contact_method': 'phone'
        }

    def test_problem_form_exists(self):
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Report your problem' in resp.content)

    def test_problem_form_shows_provider_name(self):
        resp = self.client.get(self.form_url)
        self.assertTrue(self.test_organisation.name in resp.content)

    def test_problem_form_happy_path(self):
        resp = self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertContains(resp, problem.reference_number, count=1, status_code=200)
        self.assertEqual(problem.organisation, self.test_organisation)
        self.assertEqual(problem.service, self.test_service)
        self.assertEqual(problem.public, False)
        self.assertEqual(problem.public_reporter_name, False)
        self.assertEqual(problem.description, 'This is a problem')
        self.assertEqual(problem.reporter_name, self.uuid)
        self.assertEqual(problem.reporter_email, 'steve@mysociety.org')
        self.assertEqual(problem.preferred_contact_method, 'phone')

    def test_problem_form_respects_name_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PRIVATE_NAME
        resp = self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, False)

    def test_problem_form_respects_public_privacy(self):
        self.test_problem['privacy'] = ProblemForm.PRIVACY_PUBLIC
        resp = self.client.post(self.form_url, self.test_problem)
        # Check in db
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.public, True)
        self.assertEqual(problem.public_reporter_name, True)

    def test_problem_form_errors_without_email_or_phone(self):
        del self.test_problem['reporter_email']
        del self.test_problem['reporter_phone']
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', None, 'You must provide either a phone number or an email address')

    def test_problem_form_accepts_phone_only(self):
        del self.test_problem['reporter_email']
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)

    def test_problem_form_accepts_email_only(self):
        del self.test_problem['reporter_phone']
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)

class QuestionCreateFormTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = '/choices/question/question-form/%s' % self.test_organisation.ods_code
        self.test_question = {
            'organisation': self.test_organisation.id,
            'description': 'This is a question',
            'category': 'prescriptions',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': QuestionForm.PRIVACY_PRIVATE,
            'preferred_contact_method': 'phone'
        }


    def test_question_form_exists(self):
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Ask your question' in resp.content)

    def test_question_form_shows_provider_name(self):
        resp = self.client.get(self.form_url)
        self.assertTrue(self.test_organisation.name in resp.content)

    def test_question_form_happy_path(self):
        resp = self.client.post(self.form_url, self.test_question)
        # Check in db
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertContains(resp, question.reference_number, count=1, status_code=200)
        self.assertEqual(question.organisation, self.test_organisation)
        self.assertEqual(question.public, False)
        self.assertEqual(question.public_reporter_name, False)
        self.assertEqual(question.description, 'This is a question')
        self.assertEqual(question.reporter_name, self.uuid)
        self.assertEqual(question.reporter_email, 'steve@mysociety.org')
        self.assertEqual(question.preferred_contact_method, 'phone')

    def test_question_form_respects_name_privacy(self):
        self.test_question['privacy'] = QuestionForm.PRIVACY_PRIVATE_NAME
        resp = self.client.post(self.form_url, self.test_question)
        # Check in db
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertEqual(question.public, True)
        self.assertEqual(question.public_reporter_name, False)

    def test_question_form_respects_public_privacy(self):
        self.test_question['privacy'] = QuestionForm.PRIVACY_PUBLIC
        resp = self.client.post(self.form_url, self.test_question)
        # Check in db
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertEqual(question.public, True)
        self.assertEqual(question.public_reporter_name, True)

    def test_question_form_errors_without_email_or_phone(self):
        del self.test_question['reporter_email']
        del self.test_question['reporter_phone']
        resp = self.client.post(self.form_url, self.test_question)
        self.assertFormError(resp, 'form', None, 'You must provide either a phone number or an email address')

    def test_question_form_accepts_phone_only(self):
        del self.test_question['reporter_email']
        resp = self.client.post(self.form_url, self.test_question)
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(question)

    def test_question_form_accepts_email_only(self):
        del self.test_question['reporter_phone']
        resp = self.client.post(self.form_url, self.test_question)
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(question)
