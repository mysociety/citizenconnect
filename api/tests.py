import uuid

from django.test import TestCase
from django.utils import simplejson as json
from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_organisation, create_test_service
from issues.models import Problem, Question

class APITests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.problem_uuid = uuid.uuid4().hex
        self.test_problem = {
            'organisation': self.test_organisation.ods_code,
            'service_code': self.test_service.service_code,
            'description': 'This is a problem',
            'moderated_description': 'This is a moderated problem',
            'category': 'cleanliness',
            'reporter_name': self.problem_uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'publication_status': Problem.PUBLISHED,
            'public': 1,
            'public_reporter_name': 1,
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'source':Problem.SOURCE_PHONE
        }
        self.question_uuid = uuid.uuid4().hex
        self.test_question = {
            'description': 'This is a question',
            'category': 'staff',
            'reporter_name': self.question_uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'source':Problem.SOURCE_PHONE
        }

        self.question_api_url = reverse('api-question-create')
        self.problem_api_url = reverse('api-problem-create')

    def test_question_api_happy_path(self):
        resp = self.client.post(self.question_api_url, self.test_question)
        self.assertEquals(resp.status_code, 201)

        question = Question.objects.get(reporter_name=self.question_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, question.id)

        content_json = json.loads(resp.content)
        self.assertTrue(content_json['reference_number'], expected_reference_number)
        self.assertEqual(question.description, self.test_question['description'])
        self.assertEqual(question.category, self.test_question['category'])
        self.assertEqual(question.reporter_name, self.test_question['reporter_name'])
        self.assertEqual(question.reporter_email, self.test_question['reporter_email'])
        self.assertEqual(question.reporter_phone, self.test_question['reporter_phone'])
        self.assertEqual(question.source, self.test_question['source'])

    def test_problem_api_happy_path(self):
        resp = self.client.post(self.problem_api_url, self.test_problem)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertTrue(content_json['reference_number'], expected_reference_number)
        self.assertEqual(problem.organisation, self.test_organisation)
        self.assertEqual(problem.service, self.test_service)
        self.assertEqual(problem.description, self.test_problem['description'])
        self.assertEqual(problem.moderated_description, self.test_problem['moderated_description'])
        self.assertEqual(problem.category, self.test_problem['category'])
        self.assertEqual(problem.reporter_name, self.test_problem['reporter_name'])
        self.assertEqual(problem.reporter_email, self.test_problem['reporter_email'])
        self.assertEqual(problem.reporter_phone, self.test_problem['reporter_phone'])
        self.assertEqual(problem.public, self.test_problem['public'])
        self.assertEqual(problem.public_reporter_name, True)
        self.assertEqual(problem.publication_status, True)
        self.assertEqual(problem.source, self.test_problem['source'])
        self.assertEqual(problem.moderated, Problem.MODERATED)

    def test_source_is_required(self):
        problem_without_source = self.test_problem
        del problem_without_source['source']
        resp = self.client.post(self.problem_api_url, problem_without_source)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['source'][0], 'This field is required.')

    def test_service_code_is_optional(self):
        problem_without_service = self.test_problem
        del problem_without_service['service_code']
        resp = self.client.post(self.problem_api_url, problem_without_service)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertEqual(content_json['reference_number'], expected_reference_number)
        self.assertIsNone(problem.service)

    def test_unknown_service_code_rejected(self):
        problem_with_unknown_service = self.test_problem
        problem_with_unknown_service['service_code'] = 'gibberish'
        resp = self.client.post(self.problem_api_url, problem_with_unknown_service)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['service_code'][0], 'Sorry, that service is not recognised.')

    def test_organisation_required(self):
        problem_without_organisation = self.test_problem
        del problem_without_organisation['organisation']
        resp = self.client.post(self.problem_api_url, problem_without_organisation)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['organisation'][0], 'This field is required.')

    def test_unknown_organisation_rejected(self):
        problem_with_unknown_organisation = self.test_problem
        problem_with_unknown_organisation['organisation'] = 'gibberish'
        resp = self.client.post(self.problem_api_url, problem_with_unknown_organisation)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['organisation'][0], 'Sorry, that organisation is not recognised.')

    def test_service_id_ignored(self):
        # Because we add an extra service_code field but don't exclude the
        # service field (because we need to set it in clean) we could accept
        # people posting data to the service field itself. We don't want that.
        other_service = create_test_service({'organisation': self.test_organisation, 'service_code': 'other'})
        problem_with_service_id = self.test_problem
        problem_with_service_id['service'] = other_service.id
        resp = self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEquals(problem.service, self.test_service)

    def test_service_id_ignored_even_with_empty_service_code(self):
        other_service = create_test_service({'organisation': self.test_organisation, 'service_code': 'other'})
        problem_with_service_id = self.test_problem
        problem_with_service_id['service'] = other_service.id
        del problem_with_service_id['service_code']
        resp = self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertIsNone(problem.service)

    def test_reporter_name_or_phone_is_required(self):
        problem_with_no_contact_details = self.test_problem
        del problem_with_no_contact_details['reporter_phone']
        del problem_with_no_contact_details['reporter_email']

        resp = self.client.post(self.problem_api_url, problem_with_no_contact_details)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['__all__'][0], 'You must provide either a phone number or an email address')

    def test_moderated_description_is_required_when_publishing_public_problems(self):
        public_problem_with_no_moderated_description = self.test_problem
        public_problem_with_no_moderated_description['public'] = 1
        del public_problem_with_no_moderated_description['moderated_description']
        resp = self.client.post(self.problem_api_url, public_problem_with_no_moderated_description)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['moderated_description'][0],  'You must moderate a version of the problem details when publishing public problems.')

