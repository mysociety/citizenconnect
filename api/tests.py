import uuid

from django.test import TestCase
from django.utils import simplejson as json

from organisations.tests.lib import create_test_organisation, create_test_service
from problems.models import Problem
from questions.models import Question

class APITests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.problem_uuid = uuid.uuid4().hex
        self.test_problem = {
            'organisation': self.test_organisation.id,
            'service': self.test_service.id,
            'description': 'This is a problem',
            'category': 'cleanliness',
            'reporter_name': self.problem_uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'private':False,
            'private_reporter_name':False,
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'source':Problem.SOURCE_PHONE
        }
        self.question_uuid = uuid.uuid4().hex
        self.test_question = {
            'organisation': self.test_organisation.id,
            'service': self.test_service.id,
            'description': 'This is a question',
            'category': 'prescriptions',
            'reporter_name': self.question_uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'private':False,
            'private_reporter_name':False,
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'source':Problem.SOURCE_PHONE
        }

        self.question_api_url = '/api/v0.1/question'
        self.problem_api_url = '/api/v0.1/problem'

    def test_question_api_happy_path(self):
        resp = self.client.post(self.question_api_url, self.test_question)
        self.assertEquals(resp.status_code, 201)

        question = Question.objects.get(reporter_name=self.question_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, question.id)

        content_json = json.loads(resp.content)
        self.assertTrue(content_json['reference_number'], expected_reference_number)

    def test_problem_api_happy_path(self):
        resp = self.client.post(self.problem_api_url, self.test_problem)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertTrue(content_json['reference_number'], expected_reference_number)
