from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

from organisations.tests import create_test_problem, create_test_organisation, create_review_with_age, create_problem_with_age, AuthorizationTestCase
from responses.models import ProblemResponse

from ..models import Problem
from ..lib import int_to_base32

class ProblemPublicViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemPublicViewTests, self).setUp()
        self.test_moderated_problem = create_test_problem({'organisation': self.test_organisation,
                                                           'publication_status': Problem.PUBLISHED,
                                                           'moderated_description': "A moderated description"})
        self.test_unmoderated_problem = create_test_problem({'organisation': self.test_organisation})
        self.test_private_problem = create_test_problem({'organisation': self.test_organisation,
                                                         'public': False,
                                                         'public_reporter_name': False,
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

        self.login_as(self.trust_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.superuser)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_trust_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.other_ccg_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_allowed_users(self):
        self.login_as(self.trust_user)
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

        for user in [self.other_trust_user, self.other_ccg_user]:
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

        for user in [self.other_trust_user, self.other_ccg_user]:
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

    def test_unmoderated_problem_accessible_to_allowed_uses(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.ccg_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_inaccessible_to_other_trust_user(self):
        self.login_as(self.other_trust_user)
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

    def test_anon_user_sees_moderated_description_only(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertNotContains(resp, self.test_moderated_problem.description)
        self.assertContains(resp, self.test_moderated_problem.moderated_description)


    # Test removed as part of hiding escalated states for #669. Only commented
    # out though as I'm sure we'll need to add this back in at some point.
    #
    # def test_escalated_statuses_highlighted(self):
    #     for status in Problem.ESCALATION_STATUSES:
    #         problem = create_test_problem({'organisation': self.test_organisation,
    #                                        'publication_status': Problem.PUBLISHED,
    #                                        'moderated_description': "A moderated description",
    #                                        'status': status,
    #                                        'commissioned': Problem.LOCALLY_COMMISSIONED})
    #         problem_url = reverse('problem-view', kwargs={'cobrand': 'choices',
    #                                                       'pk': problem.id})
    #         resp = self.client.get(problem_url)
    #         expected_text = '<span class="icon-arrow-up-right" aria-hidden="true"></span> This problem has been escalated'
    #         self.assertContains(resp, expected_text)

    def test_shows_open_or_closed_and_specific_status(self):
        # An open problem
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "Open")
        self.assertContains(resp, self.test_moderated_problem.get_status_display())

        # A closed problem
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
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

    def test_shows_report_link(self):
        resp = self.client.get(self.test_moderated_problem_url)
        expected_link = '<a href="/choices/feedback">Report as unsuitable</a>'
        self.assertContains(resp, expected_link)


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
        self.assertContains(resp, self.test_organisation.name, count=1)

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

    def test_form_page_records_nothing_for_a_no_answer_response(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'd',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.assertEqual(self.test_problem.happy_service, None)
        resp = self.client.get(form_page)
        self.assertEqual(resp.status_code, 200)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_service, None)

    def test_confirm_page_links_to_reviews(self):
        # Now post to it to get the confirmation page
        resp = self.client.post(self.form_page, {})
        expected_review_url = reverse('review-form',
                                      kwargs={'cobrand': 'choices',
                                              'ods_code': self.test_organisation.ods_code})
        self.assertContains(resp, 'share your experience')
        self.assertContains(resp, expected_review_url)


class HomePageTests(TestCase):

    def setUp(self):
        self.homepage_url = reverse('home', kwargs={'cobrand': 'choices'})
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        public_atts = {'publication_status': Problem.PUBLISHED}
        # Some problems and reviews
        create_problem_with_age(self.test_organisation, age=1, attributes=public_atts)
        create_review_with_age(self.test_organisation, age=2)
        create_problem_with_age(self.test_organisation, age=4, attributes=public_atts)
        create_review_with_age(self.test_organisation, age=3)
        create_review_with_age(self.test_organisation, age=5)
        public_atts.update({'moderated_description': 'Sixth item'})
        create_problem_with_age(self.test_organisation, age=6, attributes=public_atts)

    def test_homepage_exists(self):
        resp = self.client.get(self.homepage_url)
        self.assertEqual(resp.status_code, 200)

    def test_displays_last_five_problems_or_reviews(self):
        resp = self.client.get(self.homepage_url)
        self.assertContains(resp, '<h3 class="feed-list__title">', count=5, status_code=200)
        self.assertNotContains(resp, 'Sixth item')

class PublicLookupFormTests(TestCase):

    def setUp(self):
        self.homepage_url = reverse('home', kwargs={'cobrand': 'choices'})
        self.test_organisation = create_test_organisation({'ods_code': '11111'})
        self.test_problem = create_test_problem({'organisation': self.test_organisation,
                                                 'publication_status': Problem.PUBLISHED})
        self.closed_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'publication_status': Problem.PUBLISHED,
                                                   'status': Problem.RESOLVED})
        self.problem_url = reverse('problem-view', kwargs={'pk':self.test_problem.id,
                                                           'cobrand': 'choices'})
        self.closed_problem_url = reverse('problem-view', kwargs={'pk':self.closed_problem.id,
                                                                  'cobrand': 'choices'})

        self.problem_reference = '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)

    def test_happy_path(self):
        resp = self.client.post(self.homepage_url, {'reference_number': self.problem_reference})
        self.assertRedirects(resp, self.problem_url)

    def test_obvious_correction(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX.lower(), self.test_problem.id)})
        self.assertRedirects(resp, self.problem_url)

    def test_rejects_hidden_problems(self):
        self.test_problem.publication_status = Problem.HIDDEN
        self.test_problem.save()
        resp = self.client.post(self.homepage_url, {'reference_number': self.problem_reference})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not available')

    def test_form_rejects_empty_submissions(self):
        resp = self.client.post(self.homepage_url, {})
        self.assertFormError(resp, 'form', 'reference_number', 'This field is required.')

    def test_form_rejects_unknown_prefixes(self):
        resp = self.client.post(self.homepage_url, {'reference_number': 'a123'})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_unknown_problems(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}12300'.format(Problem.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no problems with that reference number')

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.homepage_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, self.closed_problem_url)
