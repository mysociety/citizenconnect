import logging

from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question
from responses.models import ProblemResponse

from .lib import BaseModerationTestCase

class BasicViewTests(BaseModerationTestCase):

    def setUp(self):
        super(BasicViewTests, self).setUp()
        self.login_as(self.case_handler)

    def test_views_exist(self):
        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_views_require_login(self):
        self.client.logout()

        for url in self.all_urls:
            expected_login_url = "{0}?next={1}".format(self.login_url, url)
            resp = self.client.get(url)
            self.assertRedirects(resp, expected_login_url)

    def test_views_inacessible_to_providers(self):
        self.client.logout()
        self.login_as(self.provider)

        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_views_inacessible_to_ccgs(self):
        self.client.logout()
        self.login_as(self.ccg_user)

        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_views_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            for url in self.all_urls:
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)

    def test_views_accessible_to_second_tier_moderators(self):
        self.client.logout()
        self.login_as(self.second_tier_moderator)

        for url in self.all_second_tier_moderator_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)


class HomeViewTests(BaseModerationTestCase):

    def setUp(self):
        super(HomeViewTests, self).setUp()

        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})

        self.login_as(self.case_handler)

    def test_issues_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.test_problem in resp.context['issues'])
        self.assertTrue(self.closed_problem in resp.context['issues'])

    def test_moderated_issues_not_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.moderated_problem not in resp.context['issues'])

    def test_issues_displayed(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.test_problem.private_summary)
        self.assertContains(resp, self.closed_problem.private_summary)

    def test_issues_link_to_moderate_form(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.problem_form_url)

class SecondTierModerationHomeViewTests(BaseModerationTestCase):

    def setUp(self):
        super(SecondTierModerationHomeViewTests, self).setUp()
        self.second_tier_moderation = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                               'requires_second_tier_moderation': True})
        self.no_second_tier_moderation = create_test_instance(Problem, {'organisation': self.test_organisation})
        self.login_as(self.second_tier_moderator)

    def test_issues_in_context(self):
        resp = self.client.get(self.second_tier_home_url)
        self.assertTrue(self.second_tier_moderation in resp.context['issues'])

    def test_issues_not_requiring_second_tier_moderation_not_in_context(self):
        resp = self.client.get(self.second_tier_home_url)
        self.assertTrue(self.no_second_tier_moderation not in resp.context['issues'])

    def test_issues_link_to_second_tier_moderate_form(self):
        resp = self.client.get(self.second_tier_home_url)
        self.second_tier_problem_form_url = reverse('second-tier-moderate-form', kwargs={'pk':self.second_tier_moderation.id})
        self.assertContains(resp, self.second_tier_problem_form_url)

class ModerateFormViewTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerateFormViewTests, self).setUp()

        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})

        self.login_as(self.case_handler)

    def test_problem_in_context(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.context['issue'], self.test_problem)

    def test_issue_data_displayed(self):
        # Add some responses to the issue too
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_problem)

        resp = self.client.get(self.problem_form_url)
        self.assertContains(resp, self.test_problem.reference_number)
        self.assertContains(resp, self.test_problem.reporter_name)
        self.assertContains(resp, self.test_problem.description)
        self.assertContains(resp, self.test_problem.organisation.name)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

    def test_moderated_issues_accepted(self):
        resp = self.client.get(reverse('moderate-form', kwargs={'pk':self.moderated_problem.id}))
        self.assertEqual(resp.status_code, 200)

    def test_closed_issues_accepted(self):
        resp = self.client.get(reverse('moderate-form', kwargs={'pk':self.closed_problem.id}))
        self.assertEqual(resp.status_code, 200)

    def test_initial_versions_set_when_form_loads(self):
        # Add some responses to the issue too
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_problem)

        self.client.get(self.problem_form_url)
        problem_session_version = self.client.session['problem_versions'][self.test_problem.id]
        self.assertEqual(problem_session_version, self.test_problem.version)
        response_session_versions = self.client.session['response_versions']
        self.assertEqual(response_session_versions[response1.id], response1.version)
        self.assertEqual(response_session_versions[response2.id], response2.version)

    def test_version_cleared_when_form_valid(self):
        # Add some responses to the issue too
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_problem)

        # Call the form to simulate a browser and get a session into self.client
        self.client.get(self.problem_form_url)
        self.assertTrue(self.test_problem.id in self.client.session['problem_versions'])
        self.assertTrue(response1.id in self.client.session['response_versions'])
        self.assertTrue(response2.id in self.client.session['response_versions'])

        # Post to the form with some new data
        form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'publish': '',
            'status': self.test_problem.status,
            'moderated': self.test_problem.moderated,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'responses-TOTAL_FORMS': 2,
            'responses-INITIAL_FORMS': 2,
            'responses-MAX_NUM_FORMS': 0,
            'responses-0-id': response1.id,
            'responses-0-response': response1.response,
            'responses-0-DELETE': False,
            'responses-1-id': response2.id,
            'responses-1-response': response2.response,
            'responses-1-DELETE': False
        }
        resp = self.client.post(self.problem_form_url, form_values)
        self.assertFalse(self.test_problem.id in self.client.session['problem_versions'])
        self.assertFalse(response1.id in self.client.session['response_versions'])
        self.assertFalse(response2.id in self.client.session['response_versions'])


class SecondTierModerateFormViewTests(BaseModerationTestCase):

    def setUp(self):
        super(SecondTierModerateFormViewTests, self).setUp()
        self.login_as(self.second_tier_moderator)

    def test_problem_in_context(self):
        resp = self.client.get(self.second_tier_problem_form_url)
        self.assertEqual(resp.context['issue'], self.test_second_tier_moderation_problem)

    def test_issues_not_requiring_second_tier_moderation_rejected(self):
        second_tier_moderation_form_url =  reverse('second-tier-moderate-form', kwargs={'pk':self.test_problem.id})
        resp = self.client.get(second_tier_moderation_form_url)
        self.assertEqual(resp.status_code, 404)
