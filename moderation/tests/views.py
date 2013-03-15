import logging

from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question
from responses.models import ProblemResponse

from .lib import BaseModerationTestCase

class BasicViewTests(BaseModerationTestCase):

    def setUp(self):
        super(BasicViewTests, self).setUp()
        self.login_as(self.test_moderator)

    def test_home_view_exists(self):
        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, 200)

    def test_lookup_view_exists(self):
        resp = self.client.get(self.lookup_url)
        self.assertEqual(resp.status_code, 200)

    def test_form_views_exist(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.status_code, 200)

    def test_confirm_view_exists(self):
        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 200)

    def test_views_require_login(self):
        self.client.logout()

        expected_login_url = "{0}?next={1}".format(self.login_url, self.home_url)
        resp = self.client.get(self.home_url)
        self.assertRedirects(resp, expected_login_url)

        expected_login_url = "{0}?next={1}".format(self.login_url, self.lookup_url)
        resp = self.client.get(self.lookup_url)
        self.assertRedirects(resp, expected_login_url)

        expected_login_url = "{0}?next={1}".format(self.login_url, self.problem_form_url)
        resp = self.client.get(self.problem_form_url)
        self.assertRedirects(resp, expected_login_url)

        expected_login_url = "{0}?next={1}".format(self.login_url, self.confirm_url)
        resp = self.client.get(self.confirm_url)
        self.assertRedirects(resp, expected_login_url)

    def test_views_innacessible_to_providers(self):
        self.client.logout()
        self.login_as(self.test_allowed_user)

        resp = self.client.get(self.home_url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(self.lookup_url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client.get(self.confirm_url)
        self.assertEqual(resp.status_code, 403)

class HomeViewTests(BaseModerationTestCase):

    def setUp(self):
        super(HomeViewTests, self).setUp()

        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})

        self.login_as(self.test_moderator)

    def test_issues_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.test_problem in resp.context['issues'])
        self.assertTrue(self.closed_problem in resp.context['issues'])

    def test_moderated_issues_not_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.moderated_problem not in resp.context['issues'])

    def test_issues_displayed(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.test_problem.summary)
        self.assertContains(resp, self.closed_problem.summary)

    def test_issues_link_to_moderate_form(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.problem_form_url)

class ModerateFormViewTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerateFormViewTests, self).setUp()

        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})

        self.login_as(self.test_moderator)

    def test_problem_in_context(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.context['message'], self.test_problem)

    def test_message_data_displayed(self):
        # Add some responses to the message too
        response1 = ProblemResponse.objects.create(response="response 1", message=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", message=self.test_problem)

        resp = self.client.get(self.problem_form_url)
        self.assertContains(resp, self.test_problem.reference_number)
        self.assertContains(resp, self.test_problem.reporter_name)
        self.assertContains(resp, self.test_problem.description)
        self.assertContains(resp, self.test_problem.organisation.name)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

    def test_moderated_issues_rejected(self):
        # Quiten down logging
        logging.disable(logging.CRITICAL)

        resp = self.client.get('/private/moderate/{0}'.format(self.moderated_problem.id))
        self.assertEqual(resp.status_code, 404)

        logging.disable(logging.NOTSET)

    def test_closed_issues_accepted(self):
        resp = self.client.get('/private/moderate/{0}'.format(self.closed_problem.id))
        self.assertEqual(resp.status_code, 200)
