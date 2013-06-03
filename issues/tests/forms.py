import uuid
import time

from django.test import TestCase
from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_organisation, create_test_service, create_test_problem

from ..models import Problem
from ..forms import ProblemForm
from ..lib import int_to_base32

from citizenconnect.browser_testing import SeleniumTestCase

class ProblemCreateFormBase(object):

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
            'preferred_contact_method': Problem.CONTACT_PHONE,
            'agree_to_terms': True,
            'elevate_priority': False,
            'website': '', # honeypot - should be blank
        }

class ProblemCreateFormTests(ProblemCreateFormBase, TestCase):

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
        self.assertEqual(problem.priority, Problem.PRIORITY_NORMAL)

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

    def test_problem_form_requires_email(self):
        # test correctly formatted
        self.test_problem['reporter_email'] = 'not an email.com'
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_email', 'Enter a valid e-mail address.')
        # test required
        del self.test_problem['reporter_email']
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_email', 'This field is required.')

    def test_problem_form_checks_phone_is_valid(self):
        self.test_problem['reporter_phone'] = 'not a number'
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', 'reporter_phone', 'Enter a valid phone number.')

    def test_problem_form_checks_phone_when_phone_preferred(self):
        del self.test_problem['reporter_phone']
        self.test_problem['preferred_contact_method'] = Problem.CONTACT_PHONE
        resp = self.client.post(self.form_url, self.test_problem)
        self.assertFormError(resp, 'form', None, 'You must provide a phone number if you prefer to be contacted by phone')

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

    def test_problem_can_be_elevated(self):
        self.test_problem['elevate_priority'] = True
        self.test_problem['category'] = 'treatment'
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.priority, Problem.PRIORITY_HIGH, 'Problem has wrong priority (should be HIGH)')

    def test_elevated_ignored_if_category_does_not_permit(self):
        self.test_problem['elevate_priority'] = True
        self.test_problem['category'] = 'parking'
        resp = self.client.post(self.form_url, self.test_problem)
        problem = Problem.objects.get(reporter_name=self.uuid)
        self.assertEqual(problem.priority, Problem.PRIORITY_NORMAL, 'Problem has wrong priority (should be NORMAL)')

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


class ProblemCreateFormBrowserTests(ProblemCreateFormBase, SeleniumTestCase):

    def is_elevate_priority_disabled(self):
        return self.driver.find_element_by_id('id_elevate_priority').get_attribute('disabled')

    def test_currently_in_care_toggling(self):
        d = self.driver
        d.get(self.full_url(self.form_url))


        # Should be disabled initially
        self.assertTrue(self.is_elevate_priority_disabled())

        # Select a category that it applies to
        d.find_element_by_css_selector('input[name="category"][value="dignity"]').click()
        self.assertFalse(self.is_elevate_priority_disabled())

        # Select a category it does not apply to
        d.find_element_by_css_selector('input[name="category"][value="parking"]').click()
        self.assertTrue(self.is_elevate_priority_disabled())


class ProblemSurveyFormTests(TestCase):

    def setUp(self):
        self.test_problem = create_test_problem({})
        self.survey_form_url = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                              'response': 'n',
                                                              'id': int_to_base32(self.test_problem.id),
                                                              'token': self.test_problem.make_token(5555)})
        self.form_values = {'happy_outcome': 'True'}

    def test_form_happy_path(self):
        resp = self.client.post(self.survey_form_url, self.form_values)
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, True)

    def test_form_records_empty_happy_outcome(self):
        resp = self.client.post(self.survey_form_url, {'happy_outcome': ''})
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, None)

    def test_form_records_false_happy_outcome(self):
        resp = self.client.post(self.survey_form_url, {'happy_outcome': 'False'})
        self.assertContains(resp, 'Thank you for taking the time to send us your feedback')
        self.test_problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(self.test_problem.happy_outcome, False)
