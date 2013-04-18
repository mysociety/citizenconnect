# Django imports
from django.test import TestCase, TransactionTestCase
from django.core.urlresolvers import reverse

from concurrency.utils import ConcurrencyTestMixin

# App imports
from issues.models import Problem, Question
from .models import ProblemResponse

from organisations.tests.lib import create_test_instance, create_test_organisation, AuthorizationTestCase
from moderation.tests.lib import BaseModerationTestCase


# from organisations.models import Organisation


class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})
        self.login_as(self.case_handler)

        self.lookup_url           = reverse('response-lookup')
        self.problem_response_url = reverse('response-form', kwargs={'pk':self.test_problem.id})

    def test_happy_path(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)})
        self.assertRedirects(resp, self.problem_response_url)

    def test_obvious_correction(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX.lower(), self.test_problem.id)})
        self.assertRedirects(resp, self.problem_response_url)

    def test_form_rejects_empty_submissions(self):
        resp = self.client.post(self.lookup_url, {})
        self.assertFormError(resp, 'form', 'reference_number', 'This field is required.')

    def test_form_rejects_unknown_prefixes(self):
        resp = self.client.post(self.lookup_url, {'reference_number': 'a123'})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_unknown_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}12300'.format(Problem.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no problems with that reference number')

    def test_form_rejects_questions(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Question.PREFIX, self.test_question.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_allows_moderated_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.moderated_problem.id)})
        self.assertRedirects(resp, '/private/response/{0}'.format(self.moderated_problem.id))

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, '/private/response/{0}'.format(self.closed_problem.id))


class ResponseFormTests(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        super(ResponseFormTests, self).setUp()
        self.problem = create_test_instance(Problem, {'organisation':self.test_organisation})
        self.response_form_url = reverse('response-form', kwargs={'pk':self.problem.id})
        self.login_as(self.provider)
        # The form assumes a session variable is set, because it is when you load the form
        # in a browser, so we call the page to set it here.
        self.client.get(self.response_form_url)

    def test_form_creates_problem_response(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        response = self.problem.responses.all()[0]
        self.assertEqual(self.problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)

    def test_form_creates_problem_response_and_saves_status(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        response = self.problem.responses.all()[0]
        self.assertEqual(self.problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)
        self.assertEqual(self.problem.status, Problem.RESOLVED)

    def test_form_allows_empty_response_for_status_change(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(self.problem.responses.count(), 0)
        self.assertEqual(self.problem.status, Problem.RESOLVED)

    def test_form_warns_about_response_during_status_change(self):
        response_text = 'I didn\'t mean to respond'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertFormError(resp, 'form', 'response', 'You cannot submit a response if you\'re just updating the status. Please delete the text in the response field or use the "Respond" button.')

    def test_form_requires_text_for_responses(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertFormError(resp, 'form', 'response', 'This field is required.')

    def test_form_shows_response_confirmation_with_link(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "response has been published online")
        self.assertContains(resp, reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code}))

    def test_form_shows_issue_confirmation_with_link(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "the Problem status has been updated")
        self.assertContains(resp, reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code}))

    def test_initial_version_set_when_form_loads(self):
        self.client.get(self.response_form_url)
        session_version = self.client.session['object_versions'][self.problem.id]
        self.assertEqual(session_version, self.problem.version)

    def test_form_checks_versions(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.problem.id] -= 3000
        session.save()
        # Now post to the form, we should be rejected
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertFormError(resp, 'form', None, 'Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')

    def test_form_resets_version_if_versions_dont_match(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.problem.id] -= 3000
        session.save()
        # Now post to the form, we should be rejected and our change to the issue
        # status should be reset
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        session_version = self.client.session['object_versions'][self.problem.id]
        self.assertEqual(session_version, self.problem.version)

    def test_version_cleared_when_form_valid(self):
        # Call the form to simulate a browser and get a session into self.client
        self.client.get(self.response_form_url)
        self.assertTrue(self.problem.id in self.client.session['object_versions'])
        # Post to the form with some new data
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'respond': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.problem.id in self.client.session['object_versions'])

class ResponseFormViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ResponseFormViewTests, self).setUp()
        self.problem = create_test_instance(Problem, {'organisation': self.test_organisation})
        self.response_form_url = reverse('response-form', kwargs={'pk':self.problem.id})
        self.login_as(self.provider)

    def test_response_page_exists(self):
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_response_form_contains_issue_data(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, self.problem.reference_number)
        self.assertContains(resp, self.problem.issue_type)
        self.assertContains(resp, self.problem.reporter_name)
        self.assertContains(resp, self.problem.description)

    def test_response_form_display_no_responses_message(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, 'No responses')

    def test_response_form_displays_previous_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response='response 1', issue=self.problem)
        response2 = ProblemResponse.objects.create(response='response 2', issue=self.problem)
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

    def test_response_form_requires_login(self):
        self.client.logout()
        expected_login_url = "{0}?next={1}".format(reverse('login'), self.response_form_url)
        resp = self.client.get(self.response_form_url)
        self.assertRedirects(resp, expected_login_url)

    def test_other_providers_cant_respond(self):
        self.client.logout()
        self.login_as(self.other_provider)
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 403)

    def test_other_ccgs_cant_respond(self):
        self.client.logout()
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 403)

    def test_customer_contact_centre_users_can_respond(self):
        self.client.logout()
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_version_cleared_when_form_valid_even_if_no_response(self):
        # The view has to call the unset method when no response is given
        # because it doesn't call form.save()

        # Call the form to simulate a browser and get a session into self.client
        self.client.get(self.response_form_url)
        self.assertTrue(self.problem.id in self.client.session['object_versions'])
        # Post to the form with some new data
        response_text = 'This problem is solved'
        test_form_values = {
            'response':'',
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'status': ''
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.problem.id in self.client.session['object_versions'])

    def test_ISSUE_344_problem_response_access_different_to_problem_access(self):
        # There was a bug where access to the response page was calling
        # organisations.auth.check_problem_access(), but for published
        # public problems, that returns true for _everyone_, so any
        # authenticated user could respond (authenticated only because we
        # had login_required on the view)

        # Add a public published problem
        public_published_problem = create_test_instance(Problem,
                                                        {
                                                            'organisation': self.test_organisation,
                                                            'public': True,
                                                            'status': Problem.ACKNOWLEDGED,
                                                            'publication_status': Problem.PUBLISHED,
                                                            'moderated': Problem.MODERATED
                                                        })
        form_which_should_403_for_other_providers = reverse('response-form', kwargs={'pk':public_published_problem.id})
        self.client.logout()
        self.login_as(self.other_provider)
        resp = self.client.get(form_which_should_403_for_other_providers)
        self.assertEqual(resp.status_code, 403) # This was a 200 with the bug

    def test_response_form_contains_moderated_description_and_description(self):
        # When a superuser is viewing the page, if there is a moderated
        # description then that should be shown in addition to the regular
        # description.
        moderated_problem = create_test_instance(Problem,
            {
                'organisation': self.test_organisation,
                'public': True,
                'status': Problem.ACKNOWLEDGED,
                'publication_status': Problem.PUBLISHED,
                'moderated': Problem.MODERATED,
                'description': "A description",
                'moderated_description': "A moderated description",
            })

        response_form_url = reverse('response-form', kwargs={'pk':moderated_problem.id})
        resp = self.client.get(response_form_url)
        self.assertContains(resp, moderated_problem.description)
        self.assertContains(resp, moderated_problem.moderated_description)


class ResponseModelTests(TransactionTestCase, ConcurrencyTestMixin):

    def setUp(self):
        self.problem = create_test_instance(Problem, {})
        # These are needed for ConcurrencyTestMixin to run its' tests
        self.concurrency_model = ProblemResponse
        self.concurrency_kwargs = {'response': 'A response', 'issue': self.problem}
