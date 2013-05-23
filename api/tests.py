import uuid
import base64

from django.test import TestCase
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.conf import settings

from organisations.tests.lib import create_test_organisation, create_test_service
from issues.models import Problem


class ProblemAPITests(TestCase):

    def setUp(self):
        credentials = base64.b64encode('{0}:{1}'.format(settings.API_BASICAUTH_USERNAME, settings.API_BASICAUTH_PASSWORD))
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials
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
            'source': Problem.SOURCE_PHONE,
            'requires_second_tier_moderation': 0,
            'breach': 1,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'relates_to_previous_problem': True,
            'priority': Problem.PRIORITY_HIGH,
            'escalated': 1
        }

        self.problem_api_url = reverse('api-problem-create')

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
        self.assertEqual(problem.requires_second_tier_moderation, False)
        self.assertEqual(problem.breach, True)
        self.assertEqual(problem.commissioned, Problem.NATIONALLY_COMMISSIONED)
        self.assertEqual(problem.relates_to_previous_problem, True)
        self.assertEqual(problem.priority, Problem.PRIORITY_HIGH)
        self.assertEqual(problem.status, Problem.ESCALATED)

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
        self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEquals(problem.service, self.test_service)

    def test_service_id_ignored_even_with_empty_service_code(self):
        other_service = create_test_service({'organisation': self.test_organisation, 'service_code': 'other'})
        problem_with_service_id = self.test_problem
        problem_with_service_id['service'] = other_service.id
        del problem_with_service_id['service_code']
        self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertIsNone(problem.service)

    def test_email_is_required(self):
        problem_with_no_email = self.test_problem
        del problem_with_no_email['reporter_email']

        resp = self.client.post(self.problem_api_url, problem_with_no_email)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['reporter_email'][0], 'This field is required.')

    def test_phone_is_required_if_phone_is_preferred(self):
        problem_with_no_phone = self.test_problem
        del problem_with_no_phone['reporter_phone']

        resp = self.client.post(self.problem_api_url, problem_with_no_phone)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['__all__'][0], 'You must provide a phone number if you prefer to be contacted by phone')

    def test_moderated_description_is_required_when_publishing_public_problems(self):
        public_problem_with_no_moderated_description = self.test_problem
        public_problem_with_no_moderated_description['public'] = 1
        del public_problem_with_no_moderated_description['moderated_description']
        resp = self.client.post(self.problem_api_url, public_problem_with_no_moderated_description)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['moderated_description'][0],  'You must moderate a version of the problem details when publishing public problems.')

    def test_problem_cannot_be_published_if_requires_second_tier_moderation(self):
        problem_requiring_second_tier_moderation = self.test_problem
        problem_requiring_second_tier_moderation['requires_second_tier_moderation'] = 1
        resp = self.client.post(self.problem_api_url, problem_requiring_second_tier_moderation)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['publication_status'][0], 'A problem that requires second tier moderation cannot be published.')

    def test_preferred_contact_method_is_optional_and_defaults_to_email(self):
        problem_without_preferred_contact_method = self.test_problem
        del problem_without_preferred_contact_method['preferred_contact_method']
        resp = self.client.post(self.problem_api_url, problem_without_preferred_contact_method)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(problem.preferred_contact_method, problem.CONTACT_EMAIL)

    def test_commissioned_is_required(self):
        problem_without_commissioned = self.test_problem
        del problem_without_commissioned['commissioned']
        resp = self.client.post(self.problem_api_url, problem_without_commissioned)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['commissioned'][0],  'This field is required.')

    def test_commissioned_does_not_accept_non_choice_value(self):
        problem_with_non_choice_commissioned_value = self.test_problem
        problem_with_non_choice_commissioned_value['commissioned'] = 99
        resp = self.client.post(self.problem_api_url, problem_with_non_choice_commissioned_value)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['commissioned'][0],  'Select a valid choice. 99 is not one of the available choices.')

    def test_source_does_not_accept_non_choice_value(self):
        problem_with_non_choice_source_value = self.test_problem
        problem_with_non_choice_source_value['source'] = 'telepathy'
        resp = self.client.post(self.problem_api_url, problem_with_non_choice_source_value)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['source'][0],  u"Value u'telepathy' is not a valid choice.")

    def test_priority_is_optional(self):
        problem_without_priority = self.test_problem
        del problem_without_priority['priority']
        resp = self.client.post(self.problem_api_url, problem_without_priority)
        self.assertEquals(resp.status_code, 201)

    def test_priority_checks_category_is_permitted(self):
        problem_with_invalid_category = self.test_problem
        problem_with_invalid_category['category'] = 'parking'
        resp = self.client.post(self.problem_api_url, problem_with_invalid_category)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = json.loads(content_json['errors'])
        self.assertEqual(errors['priority'][0],  u"The problem is not in a category which permits setting of a high priority.")

    def test_escalated_is_optional(self):
        problem_without_escalated = self.test_problem
        del problem_without_escalated['escalated']
        resp = self.client.post(self.problem_api_url, problem_without_escalated)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertEqual(content_json['reference_number'], expected_reference_number)
        self.assertEqual(problem.status, Problem.NEW)

    def test_status_is_ignored(self):
        self.test_problem['status'] = Problem.ACKNOWLEDGED
        del self.test_problem['escalated']
        resp = self.client.post(self.problem_api_url, self.test_problem)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertEqual(content_json['reference_number'], expected_reference_number)
        self.assertEqual(problem.status, Problem.NEW)

    def test_publication_status_is_optional_and_defaults_to_hidden(self):
        del self.test_problem['publication_status']
        resp = self.client.post(self.problem_api_url, self.test_problem)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(problem.publication_status, problem.HIDDEN)

    def test_returns_unauthorized_without_basic_auth(self):
        del self.client.defaults['HTTP_AUTHORIZATION']
        resp = self.client.post(self.problem_api_url, self.test_problem)
        self.assertEquals(resp.status_code, 401)
