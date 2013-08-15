import uuid
import base64
import os

from django.test import TestCase
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings

from organisations.tests.lib import create_test_organisation, create_test_service
from issues.models import Problem


class ProblemAPITests(TestCase):

    def setUp(self):
        super(ProblemAPITests, self).setUp()
        credentials = base64.b64encode('{0}:{1}'.format(settings.API_BASICAUTH_USERNAME, settings.API_BASICAUTH_PASSWORD))
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_service = create_test_service({'organisation': self.test_organisation})
        # Create a unique name, to use in queries rather than relying
        # on primary key increments
        self.problem_uuid = uuid.uuid4().hex
        self.test_problem_defaults = {
            'organisation': self.test_organisation.ods_code,
            'service_code': self.test_service.service_code,
            'description': 'This is a problem',
            'moderated_description': 'This is a moderated problem',
            'category': 'cleanliness',
            'reporter_name': self.problem_uuid,
            'reporter_email': 'steve@mysociety.org',
            'reporter_phone': '01111 111 111',
            'public': 1,
            'public_reporter_name': 1,
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'source': Problem.SOURCE_PHONE,
            'requires_second_tier_moderation': 0,
            'breach': 1,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'priority': Problem.PRIORITY_HIGH
        }

        self.problem_api_url = reverse('api-problem-create')

        fixtures_dir = os.path.join(settings.PROJECT_ROOT, 'issues', 'tests', 'fixtures')
        self.jpg = open(os.path.join(fixtures_dir, 'test.jpg'))
        self.bmp = open(os.path.join(fixtures_dir, 'test.bmp'))
        self.gif = open(os.path.join(fixtures_dir, 'test.gif'))

    def tearDown(self):
        self.jpg.close()
        self.gif.close()
        self.bmp.close()

    def test_problem_api_happy_path(self):
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertTrue(content_json['reference_number'], expected_reference_number)
        self.assertEqual(problem.organisation, self.test_organisation)
        self.assertEqual(problem.service, self.test_service)
        self.assertEqual(problem.description, self.test_problem_defaults['description'])
        self.assertEqual(problem.moderated_description, self.test_problem_defaults['moderated_description'])
        self.assertEqual(problem.category, self.test_problem_defaults['category'])
        self.assertEqual(problem.reporter_name, self.test_problem_defaults['reporter_name'])
        self.assertEqual(problem.reporter_email, self.test_problem_defaults['reporter_email'])
        self.assertEqual(problem.reporter_phone, self.test_problem_defaults['reporter_phone'])
        self.assertEqual(problem.public, self.test_problem_defaults['public'])
        self.assertEqual(problem.public_reporter_name, True)
        self.assertEqual(problem.source, self.test_problem_defaults['source'])
        self.assertEqual(problem.publication_status, problem.PUBLISHED)
        self.assertEqual(problem.requires_second_tier_moderation, False)
        self.assertEqual(problem.breach, True)
        self.assertEqual(problem.commissioned, Problem.NATIONALLY_COMMISSIONED)
        self.assertEqual(problem.priority, Problem.PRIORITY_HIGH)
        self.assertEqual(problem.status, Problem.NEW)
        self.assertEqual(problem.confirmation_sent, None)
        self.assertEqual(problem.confirmation_required, False)
        self.assertEqual(problem.cobrand, settings.ALLOWED_COBRANDS[0])

    def test_source_is_required(self):
        problem_without_source = self.test_problem_defaults
        del problem_without_source['source']
        resp = self.client.post(self.problem_api_url, problem_without_source)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['source'][0], 'This field is required.')

    def test_service_code_is_optional(self):
        problem_without_service = self.test_problem_defaults
        del problem_without_service['service_code']
        resp = self.client.post(self.problem_api_url, problem_without_service)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertEqual(content_json['reference_number'], expected_reference_number)
        self.assertIsNone(problem.service)

    def test_unknown_service_code_rejected(self):
        problem_with_unknown_service = self.test_problem_defaults
        problem_with_unknown_service['service_code'] = 'gibberish'
        resp = self.client.post(self.problem_api_url, problem_with_unknown_service)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['service_code'][0], 'Sorry, that service is not recognised.')

    def test_organisation_required(self):
        problem_without_organisation = self.test_problem_defaults
        del problem_without_organisation['organisation']
        resp = self.client.post(self.problem_api_url, problem_without_organisation)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['organisation'][0], 'This field is required.')

    def test_unknown_organisation_rejected(self):
        problem_with_unknown_organisation = self.test_problem_defaults
        problem_with_unknown_organisation['organisation'] = 'gibberish'
        resp = self.client.post(self.problem_api_url, problem_with_unknown_organisation)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['organisation'][0], 'Sorry, that organisation is not recognised.')

    def test_service_id_ignored(self):
        # Because we add an extra service_code field but don't exclude the
        # service field (because we need to set it in clean) we could accept
        # people posting data to the service field itself. We don't want that.
        other_service = create_test_service({'organisation': self.test_organisation, 'service_code': 'other'})
        problem_with_service_id = self.test_problem_defaults
        problem_with_service_id['service'] = other_service.id
        self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEquals(problem.service, self.test_service)

    def test_service_id_ignored_even_with_empty_service_code(self):
        other_service = create_test_service({'organisation': self.test_organisation, 'service_code': 'other'})
        problem_with_service_id = self.test_problem_defaults
        problem_with_service_id['service'] = other_service.id
        del problem_with_service_id['service_code']
        self.client.post(self.problem_api_url, problem_with_service_id)
        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertIsNone(problem.service)

    def test_one_or_both_of_reporter_email_or_phone_is_required(self):
        test_problem_data = self.test_problem_defaults
        del test_problem_data['reporter_phone']
        del test_problem_data['reporter_email']

        # Try with neither
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['__all__'][0], 'You must provide either a phone number or an email address')

        # Try with just email
        test_problem_data['reporter_email'] = 'joe@foo.com'
        test_problem_data['preferred_contact_method'] = Problem.CONTACT_EMAIL
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 201, resp.content)

        # Try with just phone
        del test_problem_data['reporter_email']
        test_problem_data['reporter_phone'] = '01234 567 890'
        test_problem_data['preferred_contact_method'] = Problem.CONTACT_PHONE
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 201, resp.content)

    def test_moderated_description_is_required_when_publishing_public_problems(self):
        public_problem_with_no_moderated_description = self.test_problem_defaults
        public_problem_with_no_moderated_description['public'] = 1
        del public_problem_with_no_moderated_description['moderated_description']
        resp = self.client.post(self.problem_api_url, public_problem_with_no_moderated_description)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['moderated_description'][0],  'You must moderate a version of the problem details when publishing public problems.')

    def test_publication_status_is_always_set_to_to_published(self):
        self.test_problem_defaults['publication_status'] = Problem.REJECTED
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(problem.publication_status, problem.PUBLISHED)


    def test_problem_set_to_not_moderated_if_requires_second_tier_moderation(self):
        problem_requiring_second_tier_moderation = self.test_problem_defaults
        problem_requiring_second_tier_moderation['requires_second_tier_moderation'] = 1
        resp = self.client.post(self.problem_api_url, problem_requiring_second_tier_moderation)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(problem.publication_status, Problem.NOT_MODERATED)

    def test_preferred_contact_method_defaults_correctly(self):
        test_problem_data = self.test_problem_defaults
        del test_problem_data['preferred_contact_method']

        # Try with both
        test_problem_data['reporter_name'] = 'both'
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 201, resp.content)
        problem = Problem.objects.get(reporter_name=test_problem_data['reporter_name'])
        self.assertEqual(problem.preferred_contact_method, Problem.CONTACT_EMAIL)

        # Try with just email
        test_problem_data['reporter_name'] = 'just email'
        del test_problem_data['reporter_phone']
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 201, resp.content)
        problem = Problem.objects.get(reporter_name=test_problem_data['reporter_name'])
        self.assertEqual(problem.preferred_contact_method, Problem.CONTACT_EMAIL)

        # Try with just phone
        test_problem_data['reporter_name'] = 'just phone'
        del test_problem_data['reporter_email']
        test_problem_data['reporter_phone'] = '01234 567 890'
        resp = self.client.post(self.problem_api_url, test_problem_data)
        self.assertEquals(resp.status_code, 201, resp.content)
        problem = Problem.objects.get(reporter_name=test_problem_data['reporter_name'])
        self.assertEqual(problem.preferred_contact_method, Problem.CONTACT_PHONE)

    def test_commissioned_is_required(self):
        problem_without_commissioned = self.test_problem_defaults
        del problem_without_commissioned['commissioned']
        resp = self.client.post(self.problem_api_url, problem_without_commissioned)
        self.assertEquals(resp.status_code, 400)

        content_json = json.loads(resp.content)
        errors = content_json['errors']
        self.assertEqual(errors['commissioned'][0],  'This field is required.')

    def test_commissioned_does_not_accept_non_choice_value(self):
        problem_with_non_choice_commissioned_value = self.test_problem_defaults
        problem_with_non_choice_commissioned_value['commissioned'] = 99
        resp = self.client.post(self.problem_api_url, problem_with_non_choice_commissioned_value)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = content_json['errors']
        self.assertEqual(errors['commissioned'][0],  'Select a valid choice. 99 is not one of the available choices.')

    def test_source_does_not_accept_non_choice_value(self):
        problem_with_non_choice_source_value = self.test_problem_defaults
        problem_with_non_choice_source_value['source'] = 'telepathy'
        resp = self.client.post(self.problem_api_url, problem_with_non_choice_source_value)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = content_json['errors']
        self.assertEqual(errors['source'][0],  u"Value u'telepathy' is not a valid choice.")

    def test_priority_is_optional(self):
        problem_without_priority = self.test_problem_defaults
        del problem_without_priority['priority']
        resp = self.client.post(self.problem_api_url, problem_without_priority)
        self.assertEquals(resp.status_code, 201)

    def test_priority_checks_category_is_permitted(self):
        problem_with_invalid_category = self.test_problem_defaults
        problem_with_invalid_category['category'] = 'parking'
        resp = self.client.post(self.problem_api_url, problem_with_invalid_category)
        self.assertEquals(resp.status_code, 400)
        content_json = json.loads(resp.content)

        errors = content_json['errors']
        self.assertEqual(errors['priority'][0],  u"The problem is not in a category which permits setting of a high priority.")

    def test_status_is_ignored(self):
        self.test_problem_defaults['status'] = Problem.ACKNOWLEDGED
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        expected_reference_number = '{0}{1}'.format(Problem.PREFIX, problem.id)

        content_json = json.loads(resp.content)
        self.assertEqual(content_json['reference_number'], expected_reference_number)
        self.assertEqual(problem.status, Problem.NEW)

    def test_returns_unauthorized_without_basic_auth(self):
        del self.client.defaults['HTTP_AUTHORIZATION']
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 401)

    def test_returns_unauthorized_with_wrong_basic_auth(self):
        credentials = base64.b64encode('incorrect:authentication')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 401)

    def test_returns_authorized_with_proxied_auth(self):
        # Test the auth passes when a proxy authenticates for us
        del self.client.defaults['HTTP_AUTHORIZATION']
        self.client.defaults['AUTH_TYPE'] = 'Basic'
        self.client.defaults['REMOTE_USER'] = settings.API_BASICAUTH_USERNAME
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

    @override_settings(MAX_IMAGES_PER_PROBLEM=3)
    def test_api_accepts_images(self):
        self.test_problem_defaults['images_0'] = self.jpg
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(1, problem.images.count())

    @override_settings(MAX_IMAGES_PER_PROBLEM=3)
    def test_api_accepts_multiple_images(self):
        self.test_problem_defaults['images_0'] = self.jpg
        self.test_problem_defaults['images_1'] = self.bmp
        self.test_problem_defaults['images_2'] = self.gif
        resp = self.client.post(self.problem_api_url, self.test_problem_defaults)
        self.assertEquals(resp.status_code, 201)

        problem = Problem.objects.get(reporter_name=self.problem_uuid)
        self.assertEqual(3, problem.images.count())
