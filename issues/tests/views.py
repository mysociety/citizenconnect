from django.test import TestCase
from django.core.urlresolvers import reverse

from organisations.tests import create_test_problem, AuthorizationTestCase
from responses.models import ProblemResponse

from ..models import Problem
from ..lib import int_to_base32


class ProblemPublicViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemPublicViewTests, self).setUp()
        self.test_moderated_problem = create_test_problem({'organisation': self.test_organisation,
                                                           'moderated': Problem.MODERATED,
                                                           'publication_status': Problem.PUBLISHED,
                                                           'moderated_description': "A moderated description"})
        self.test_unmoderated_problem = create_test_problem({'organisation': self.test_organisation})
        self.test_private_problem = create_test_problem({'organisation': self.test_organisation,
                                                         'public': False,
                                                         'public_reporter_name': False,
                                                         'moderated': Problem.MODERATED,
                                                         'publication_status': Problem.PUBLISHED})

        self.test_moderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_moderated_problem.id,
                                                                          'cobrand': 'choices'})
        self.test_unmoderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_unmoderated_problem.id,
                                                                            'cobrand': 'choices'})
        self.test_private_problem_url = reverse('problem-view', kwargs={'pk': self.test_private_problem.id,
                                                                        'cobrand': 'choices'})

    def test_public_problem_page_exists(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, self.test_organisation.name, count=2, status_code=200)

    def test_public_problem_displays_responses(self):
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_moderated_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_moderated_problem)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_problem_displays_empty_response_message(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "No responses", count=1, status_code=200)

    def test_public_problem_accessible_to_everyone(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.provider)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.superuser)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_provider)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_allowed_users(self):
        self.login_as(self.provider)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.other_provider)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_inaccessible_to_other_ccg_user(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_pals_user(self):
        self.login_as(self.pals)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_accessible_to_allowed_uses(self):
        self.login_as(self.provider)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.other_provider)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_inaccessible_to_other_ccg_user(self):
        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_unmoderated_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_accessible_to_pals_user(self):
        self.login_as(self.pals)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_anon_user_sees_moderated_description_only(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, self.test_moderated_problem.description)
        self.assertContains(resp, self.test_moderated_problem.moderated_description)

    def test_escalated_statuses_highlighted(self):
        for status in Problem.ESCALATION_STATUSES:
            problem = create_test_problem({'organisation': self.test_organisation,
                                           'moderated': Problem.MODERATED,
                                           'publication_status': Problem.PUBLISHED,
                                           'moderated_description': "A moderated description",
                                           'status': status,
                                           'commissioned': Problem.LOCALLY_COMMISSIONED})
            problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                          'pk': problem.id})
            resp = self.client.get(problem_url)
            expected_text = '<span class="icon-warning"></span>{0}'.format(problem.get_status_display())
            self.assertContains(resp, expected_text)


class ProblemProviderPickerTests(TestCase):

    def setUp(self):
        pick_provider_url = reverse('problems-pick-provider', kwargs={'cobrand': 'choices'})
        self.results_url = "{0}?organisation_type={1}&location={2}".format(pick_provider_url, 'gppractices', 'London')

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)


class ProblemSurveyTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemSurveyTests, self).setUp()
        self.test_problem = create_test_problem({'organisation': self.test_organisation})
        self.form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                        'response': 'n',
                                                        'id': int_to_base32(self.test_problem.id),
                                                        'token': self.test_problem.make_token(5555)})

    def test_form_page_exists(self):
        resp = self.client.get(self.form_page)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Thanks for your feedback...and another question.', count=1, status_code=200)

    def test_form_page_returns_a_404_for_a_non_existent_problem(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'n',
                                                   'id': int_to_base32(-20),
                                                   'token': self.test_problem.make_token(5555)})
        resp = self.client.get(form_page)
        self.assertEqual(resp.status_code, 404)

    def test_form_page_records_the_happy_service_no_response(self):
        self.assertEqual(self.test_problem.happy_service, None)
        self.client.get(self.form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_service, False)

    def test_form_page_records_the_happy_service_yes_response(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'y',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.assertEqual(self.test_problem.happy_service, None)
        self.client.get(form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_service, True)
