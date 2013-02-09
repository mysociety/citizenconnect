import uuid

from django.test import TestCase

from .models import Question
from .forms import QuestionForm
from organisations.tests import MockedChoicesAPITest

class QuestionTests(MockedChoicesAPITest):

    def setUp(self):

        super(QuestionTests, self).setUp()
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = '/choices/question/question-form/gppractices/12702'
        self.test_question = {
            'organisation_type': 'gppractices',
            'choices_id': 12702,
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
        self.assertTrue('Test Organisation Name' in resp.content)

    def test_question_form_happy_path(self):
        resp = self.client.post(self.form_url, self.test_question)
        self.assertRedirects(resp, '/choices/question/question-confirm')
        # Check in db
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertEqual(question.organisation_type, 'gppractices')
        self.assertEqual(question.choices_id, 12702)
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
