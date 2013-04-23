import uuid

from django.test import TestCase
from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_organisation, create_test_service, create_test_instance

from ..models import Problem, Question
from ..forms import ProblemForm, QuestionForm
from ..lib import int_to_base32

class ProblemCreateFormTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.other_organisation = create_test_organisation({'ods_code': '22222'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        self.other_service = create_test_service({'organisation': self.other_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = reverse('problem-form', kwargs={'ods_code': self.test_organisation.ods_code,
                                                        'cobrand': 'choices'})
        self.test_problem = {
            'organisation': self.test_organisation.id,
            'service': self.test_service.id,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'privacy': ProblemForm.PRIVACY_PRIVATE,
            'preferred_contact_method': 'phone',
            'agree_to_terms': True,
            'website': '', # honeypot - should be blank
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
        self.assertContains(resp, problem.reference_number, count=2, status_code=200)
        self.assertEqual(problem.organisation, self.test_organisation)
        self.assertEqual(problem.service, self.test_service)
        self.assertEqual(problem.public, False)
        self.assertEqual(problem.public_reporter_name, False)
        self.assertEqual(problem.description, 'This is a problem')
        self.assertEqual(problem.reporter_name, self.uuid)
        self.assertEqual(problem.reporter_email, 'steve@mysociety.org')
        self.assertEqual(problem.preferred_contact_method, 'phone')
        self.assertEqual(problem.relates_to_previous_problem, False)

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
        # Set the preferred contact method to email, else the validation will fail
        self.test_problem['preferred_contact_method'] = Problem.CONTACT_EMAIL
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertIsNotNone(problem)

    def test_problem_form_requires_tandc_agreement(self):
        self.test_problem['agree_to_terms'] = False
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'agree_to_terms', 'You must agree to the terms and conditions to use this service.')

    def test_problem_form_requires_name(self):
        del self.test_problem['reporter_name']
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_name', 'This field is required.')

    def test_problem_form_saves_cobrand(self):
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.cobrand, 'choices')

    def test_problem_form_fails_if_website_given(self):
        spam_problem = self.test_problem.copy()
        spam_problem['website'] = 'http://cheap-drugs.com/'
        resp = self.client.post(self.form_url, spam_problem)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('has been rejected' in resp.content)


class QuestionCreateFormTests(TestCase):

    def setUp(self):
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.uuid = uuid.uuid4().hex
        self.form_url = reverse('question-form', kwargs={'cobrand':'choices'})
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_question = {
            'description': 'This is a question',
            'postcode': 'BS32 4NF',
            'reporter_name': self.uuid,
            'reporter_email': 'steve@mysociety.org',
            'agree_to_terms': True
        }


    def test_question_form_exists(self):
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('Ask your question' in resp.content)

    def test_question_form_happy_path(self):
        resp = self.client.post(self.form_url, self.test_question)
        # Check in db
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertContains(resp, question.reference_number, count=1, status_code=200)
        self.assertEqual(question.description, 'This is a question')
        self.assertEqual(question.postcode, 'BS324NF')
        self.assertEqual(question.reporter_name, self.uuid)
        self.assertEqual(question.reporter_email, 'steve@mysociety.org')

    def test_question_form_errors_without_email(self):
        del self.test_question['reporter_email']
        resp = self.client.post(self.form_url, self.test_question)
        self.assertFormError(resp, 'form', 'reporter_email', 'This field is required.')

    def test_question_form_validates_postcode(self):
        self.test_question['postcode'] = 'XXX'
        resp = self.client.post(self.form_url, self.test_question)
        self.assertFormError(resp, 'form', 'postcode', 'Sorry, that doesn\'t seem to be a valid postcode.')

    def test_question_form_requires_tandc_agreement(self):
        self.test_question['agree_to_terms'] = False
        resp = self.client.post(self.form_url, self.test_question)
        self.assertFormError(resp, 'form', 'agree_to_terms', 'You must agree to the terms and conditions to use this service.')

    def test_question_form_requires_name(self):
        del self.test_question['reporter_name']
        resp = self.client.post(self.form_url, self.test_question)
        self.assertFormError(resp, 'form', 'reporter_name', 'This field is required.')

    def test_organisation_is_accepted(self):
        self.test_question['organisation'] = self.test_organisation.id
        resp = self.client.post(self.form_url, self.test_question)
        question = Question.objects.get(reporter_name=self.uuid)
        self.assertEqual(question.organisation, self.test_organisation)

def QuestionUpdateFormTests(AuthorizationTestCase):

    def setUp(self):
        self.test_question = create_test_instance(Question, {})
        self.form_url = reverse('question-update', kwargs={'pk':self.test_question.id})

    def test_form_happy_path(self):
        self.login_as(self.question_answerer)
        resp = self.client.post(self.form_url, {'response':'test response',
                                                'status': Question.RESOLVED})

        self.assertContains(resp, 'Thank you, the question has been updated.')
        self.test_question = Question.objects.get(pk=self.test_question.id)
        self.assertEqual(self.test_question.response, 'test response')
        self.assertEqual(self.test_question.status, Question.RESOLVED)

class ProblemSurveyFormTests(TestCase):

    def setUp(self):
        self.test_problem = create_test_instance(Problem, {})
        self.survey_form_url = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                              'response': 'n',
                                                              'id': int_to_base32(self.test_problem.id),
                                                              'token': self.test_problem.make_token(5555)})
        self.form_values = {'happy_outcome': 'True'}

    def test_form_happy_path(self):
        resp = self.client.post(self.survey_form_url, self.form_values)
        self.assertContains(resp, 'Thanks for answering our questions.')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, True)

    def test_form_records_empty_happy_outcome(self):
        resp = self.client.post(self.survey_form_url, {'happy_outcome': ''})
        self.assertContains(resp, 'Thanks for answering our questions.')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, None)

    def test_form_records_false_happy_outcome(self):
        resp = self.client.post(self.survey_form_url, {'happy_outcome': 'False'})
        self.assertContains(resp, 'Thanks for answering our questions.')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, False)
