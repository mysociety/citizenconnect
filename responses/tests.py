import os
import tempfile
import shutil

# Django imports
from django.test import TransactionTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.files.images import ImageFile

from concurrency.utils import ConcurrencyTestMixin
from sorl.thumbnail import get_thumbnail

# App imports
from issues.models import Problem, ProblemImage
from .models import ProblemResponse

from organisations.tests.lib import create_test_problem, AuthorizationTestCase
from moderation.tests.lib import BaseModerationTestCase
from issues.tests.lib import ProblemImageTestBase


class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'status': Problem.RESOLVED})
        self.moderated_problem = create_test_problem({'organisation': self.test_hospital,
                                                      'publication_status': Problem.PUBLISHED})
        self.login_as(self.case_handler)

        self.lookup_url = reverse('response-lookup')
        self.problem_response_url = reverse('response-form', kwargs={'pk': self.test_problem.id})

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

    def test_form_allows_moderated_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.moderated_problem.id)})
        self.assertRedirects(resp, '/private/response/{0}'.format(self.moderated_problem.id))

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, '/private/response/{0}'.format(self.closed_problem.id))


class ResponseFormTests(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        super(ResponseFormTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_hospital})
        self.response_form_url = reverse('response-form', kwargs={'pk': self.problem.id})
        self.login_as(self.trust_user)
        # The form assumes a session variable is set, because it is when you load the form
        # in a browser, so we call the page to set it here.
        self.client.get(self.response_form_url)

    def test_form_creates_problem_response(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
        }
        self.client.post(self.response_form_url, test_form_values)
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
        }
        self.client.post(self.response_form_url, test_form_values)
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
        }
        self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(self.problem.responses.count(), 0)
        self.assertEqual(self.problem.status, Problem.RESOLVED)

    def test_form_sets_formal_complaint(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_formal_complaint': True,
        }
        self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(self.problem.responses.count(), 0)
        self.assertEqual(self.problem.formal_complaint, True)

    def test_form_sets_formal_complaint_and_status(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'issue_formal_complaint': True,
        }
        self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        self.assertEqual(self.problem.responses.count(), 0)
        self.assertEqual(self.problem.status, Problem.RESOLVED)
        self.assertEqual(self.problem.formal_complaint, True)

    def test_form_sets_formal_complaint_status_and_response(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
            'issue_formal_complaint': True,
        }
        self.client.post(self.response_form_url, test_form_values)
        self.problem = Problem.objects.get(pk=self.problem.id)
        response = self.problem.responses.all()[0]
        self.assertEqual(self.problem.responses.count(), 1)
        self.assertEqual(response.response, response_text)
        self.assertEqual(self.problem.status, Problem.RESOLVED)
        self.assertEqual(self.problem.formal_complaint, True)

    def test_form_shows_response_confirmation_with_link(self):
        response_text = 'This problem is solved'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "response has been published online")

    def test_form_shows_issue_confirmation_with_link(self):
        response_text = ''
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "the problem status has been updated")

    def test_form_shows_both_confirmations_with_link(self):
        response_text = 'new response'
        test_form_values = {
            'response': response_text,
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "response has been published online")
        self.assertContains(resp, "the problem status has been updated")

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
        }
        self.client.post(self.response_form_url, test_form_values)
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
        }
        resp = self.client.post(self.response_form_url, test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.problem.id in self.client.session['object_versions'])


class ResponseFormViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ResponseFormViewTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_hospital})
        self.response_form_url = reverse('response-form', kwargs={'pk': self.problem.id})
        self.test_form_values = {
            'response': 'This is the response.',
            'issue': self.problem.id,
            'issue_status': Problem.RESOLVED,
        }
        self.login_as(self.trust_user)

    def test_response_page_exists(self):
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_response_form_contains_issue_data(self):
        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, self.problem.reference_number)
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

    def test_other_trusts_cant_respond(self):
        self.client.logout()
        self.login_as(self.gp_surgery_user)
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
        resp = self.client.post(self.response_form_url, self.test_form_values)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.problem.id in self.client.session['object_versions'])

    def test_ISSUE_344_problem_response_access_different_to_problem_access(self):
        # There was a bug where access to the response page was calling
        # organisations.auth.enforce_problem_access_check(), but for published
        # public problems, that returns true for _everyone_, so any
        # authenticated user could respond (authenticated only because we
        # had login_required on the view)

        # Add a public published problem
        public_published_problem = create_test_problem({
            'organisation': self.test_hospital,
            'public': True,
            'status': Problem.ACKNOWLEDGED,
            'publication_status': Problem.PUBLISHED,
        })
        form_which_should_403_for_other_trusts = reverse('response-form', kwargs={'pk': public_published_problem.id})
        self.client.logout()
        self.login_as(self.gp_surgery_user)
        resp = self.client.get(form_which_should_403_for_other_trusts)
        self.assertEqual(resp.status_code, 403)  # This was a 200 with the bug

    def test_response_form_contains_moderated_description_and_description(self):
        # When a superuser is viewing the page, if there is a moderated
        # description then that should be shown in addition to the regular
        # description.
        moderated_problem = create_test_problem(
            {
                'organisation': self.test_hospital,
                'public': True,
                'status': Problem.ACKNOWLEDGED,
                'publication_status': Problem.PUBLISHED,
                'description': "A description",
                'moderated_description': "A moderated description",
            })

        response_form_url = reverse('response-form', kwargs={'pk': moderated_problem.id})
        resp = self.client.get(response_form_url)
        self.assertContains(resp, moderated_problem.description)
        self.assertContains(resp, moderated_problem.moderated_description)

    def _change_user_and_submit(self, user_to_test_as):

        # logout, login and get the form
        self.client.logout()
        self.login_as(user_to_test_as)
        resp = self.client.get(self.response_form_url)
        self.assertEqual(resp.status_code, 200)

        # submit the form,
        resp = self.client.post(self.response_form_url, self.test_form_values)
        self.assertEqual(resp.status_code, 200)
        return resp


class ResponseFormImageTests(AuthorizationTestCase, ProblemImageTestBase):

    def setUp(self):
        super(ResponseFormImageTests, self).setUp()
        self.problem = create_test_problem({'organisation': self.test_hospital})
        self.response_form_url = reverse('response-form', kwargs={'pk': self.problem.id})
        self.login_as(self.trust_user)

    def test_problem_images_displayed(self):
        # Add some problem images
        test_image = ImageFile(self.jpg)
        image1 = ProblemImage.objects.create(problem=self.problem, image=test_image)
        image2 = ProblemImage.objects.create(problem=self.problem, image=test_image)
        expected_thumbnail1 = get_thumbnail(image1.image, '150')
        expected_thumbnail2 = get_thumbnail(image2.image, '150')
        expected_image_tag = '<img src="{0}"'

        resp = self.client.get(self.response_form_url)
        self.assertContains(resp, '<p class="info">There are <strong>2</strong> images associated with this problem report.</p>')
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail1.url))
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail2.url))


class ResponseModelTests(TransactionTestCase, ConcurrencyTestMixin):

    def setUp(self):
        self.problem = create_test_problem({})
        # These are needed for ConcurrencyTestMixin to run its' tests
        self.concurrency_model = ProblemResponse
        self.concurrency_kwargs = {'response': 'A response', 'issue': self.problem}
