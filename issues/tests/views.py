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
        self.assertContains(resp, self.test_organisation.name, count=1, status_code=200)

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

    def test_private_problem_accessible_to_other_users_but_no_details_shown(self):
        # Set the private problem details to something explicit
        self.test_private_problem.description = "Private Problem description"
        # This wouldn't happen in real life, but it's best to check!
        self.test_private_problem.moderated_description = "Moderated Private Problem description"
        self.test_private_problem.reporter_name = "Jane Doe"
        self.test_private_problem.save()

        # Try as anon user
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, self.test_private_problem.description)
        self.assertNotContains(resp, self.test_private_problem.moderated_description)
        self.assertNotContains(resp, self.test_private_problem.reporter_name)

        for user in [self.other_provider, self.other_ccg_user]:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, self.test_private_problem.description)
            self.assertNotContains(resp, self.test_private_problem.moderated_description)
            self.assertNotContains(resp, self.test_private_problem.reporter_name)

    def test_private_problem_doesnt_show_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_private_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_private_problem)

        # Try as anon user
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, response1.response)
        self.assertNotContains(resp, response2.response)

        for user in [self.other_provider, self.other_ccg_user]:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, response1.response)
            self.assertNotContains(resp, response2.response)

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
            expected_text = '<span class="icon-arrow-up-right" aria-hidden="true"></span> This problem has been escalated'
            self.assertContains(resp, expected_text)

    def test_shows_open_or_closed_and_specific_status(self):
        # An open problem
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "Open")
        self.assertContains(resp, self.test_moderated_problem.get_status_display())

        # A closed problem
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'moderated': Problem.MODERATED,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': "A moderated description",
                                                   'status': Problem.RESOLVED})
        closed_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                             'pk': self.closed_problem.id})
        resp = self.client.get(closed_problem_url)
        self.assertContains(resp, "Closed")
        self.assertContains(resp, self.closed_problem.get_status_display())

    def test_doesnt_show_priority_on_public_pages(self):
        # A low priority problem - should never show priority
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, "Priority")

        # A high priority problem
        self.high_priority_problem = create_test_problem({'organisation': self.test_organisation,
                                                          'moderated': Problem.MODERATED,
                                                          'publication_status': Problem.PUBLISHED,
                                                          'moderated_description': "A moderated description",
                                                          'status': Problem.NEW,
                                                          'priority': Problem.PRIORITY_HIGH})
        high_priority_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                                    'pk': self.high_priority_problem.id})
        resp = self.client.get(high_priority_problem_url)
        self.assertNotContains(resp, "Priority")

    def test_doesnt_show_breach_on_public_pages(self):
        # A breach problem
        self.breach_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'moderated': Problem.MODERATED,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'moderated_description': "A moderated description",
                                                   'status': Problem.NEW,
                                                   'breach': True})
        breach_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                             'pk': self.breach_problem.id})
        resp = self.client.get(breach_problem_url)
        self.assertNotContains(resp, "Breach")

    def test_doesnt_show_publication_status_on_public_pages(self):
        # A published problem
        self.published_problem = create_test_problem({'organisation': self.test_organisation,
                                                      'moderated': Problem.MODERATED,
                                                      'publication_status': Problem.PUBLISHED,
                                                      'moderated_description': "A moderated description",
                                                      'status': Problem.NEW,
                                                      'publication_status': Problem.PUBLISHED})
        published_problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
                                                                'pk': self.published_problem.id})
        resp = self.client.get(published_problem_url)
        self.assertNotContains(resp, self.published_problem.get_publication_status_display())

    def test_doesnt_show_history_on_public_pages(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, "History")

    def test_shows_formal_complaint(self):
        self.test_moderated_problem.formal_complaint = True
        self.test_moderated_problem.save()
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, '<span class="icon-warning  meta-data-list__icon-red" aria-hidden="true"></span> Formal complaint')


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
        self.assertContains(resp, 'Thanks for your feedback', count=1, status_code=200)

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

    def test_confirm_page_offers_new_problem_if_unhappy(self):
        # Load the page to say we're unhappy
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'n',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.client.get(form_page)
        # Now post to it to get the confirmation page
        resp = self.client.post(form_page, {})
        expected_form_url = reverse('problem-form',
                                    kwargs={'cobrand': 'choices',
                                            'ods_code': self.test_organisation.ods_code})
        self.assertContains(resp, 'report this as another problem')
        self.assertContains(resp, expected_form_url)

    def test_confirm_page_doesnt_offer_new_problem_if_happy(self):
        # Load the page to say we're happy
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'y',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.client.get(form_page)
        # Now post to it to get the confirmation page
        resp = self.client.post(form_page, {})
        expected_form_url = reverse('problem-form',
                                    kwargs={'cobrand': 'choices',
                                            'ods_code': self.test_organisation.ods_code})
        self.assertNotContains(resp, 'report this as another problem')
        self.assertNotContains(resp, expected_form_url)

    def test_confirm_page_links_to_reviews_if_happy(self):
        # Load the page to say we're happy
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'y',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.client.get(form_page)
        # Now post to it to get the confirmation page
        resp = self.client.post(form_page, {})
        expected_review_url = reverse('review-form',
                                      kwargs={'cobrand': 'choices',
                                              'ods_code': self.test_organisation.ods_code})
        self.assertContains(resp, 'Review and rate an NHS Service')
        self.assertContains(resp, expected_review_url)

    def test_confirm_page_doesnt_link_to_reviews_if_unhappy(self):
        # Load the page to say we're unhappy
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'n',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.client.get(form_page)
        # Now post to it to get the confirmation page
        resp = self.client.post(form_page, {})
        expected_review_url = reverse('review-form',
                                      kwargs={'cobrand': 'choices',
                                              'ods_code': self.test_organisation.ods_code})
        self.assertNotContains(resp, 'Review and rate an NHS Service')
        self.assertNotContains(resp, expected_review_url)
