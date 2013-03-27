from django.test import TestCase
from django.core.urlresolvers import reverse

from organisations.tests import create_test_instance, create_test_organisation, AuthorizationTestCase
from responses.models import ProblemResponse

from ..models import Question, Problem
from ..lib import int_to_base32

class AskQuestionViewTests(TestCase):
    def setUp(self):
        self.url = reverse('ask-question', kwargs={'cobrand':'choices'})

    def test_ask_question_page_exists(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_ask_question_page_links_to_question_form(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, '/choices/question/question-form')

    def test_ask_question_page_links_to_question_provider_picker(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, '/choices/question/pick-provider')

class QuestionCreateViewTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.url = reverse('question-form', kwargs={'cobrand':'choices'})
        self.organisation_url = reverse('question-form', kwargs={'cobrand':'choices',
                                                                 'ods_code': self.test_organisation.ods_code})

    def test_organisation_name_shown(self):
        resp = self.client.get(self.organisation_url)
        self.assertContains(resp, self.test_organisation.name)

class QuestionUpdateViewTests(AuthorizationTestCase):

    def setUp(self):
        super(QuestionUpdateViewTests, self).setUp()
        self.test_question = create_test_instance(Question, {})
        self.url = reverse('question-update', kwargs={'pk':self.test_question.id})

    def test_requires_login(self):
        expected_redirect_url = "{0}?next={1}".format(reverse('login'), self.url)
        resp = self.client.get(self.url)
        self.assertRedirects(resp, expected_redirect_url)

    def test_only_question_answerers_and_superusers_can_access(self):
        users_who_shouldnt_have_access = [self.provider,
                                          self.other_provider,
                                          self.case_handler,
                                          self.no_provider,
                                          self.pals]
        for user in users_who_shouldnt_have_access:
            self.login_as(user)
            resp = self.client.get(self.url)
            self.assertEqual(resp.status_code, 403)

        users_who_should_have_access = [self.question_answerer,
                                        self.nhs_superuser]

        for user in users_who_should_have_access:
            self.login_as(user)
            resp = self.client.get(self.url)
            self.assertEqual(resp.status_code, 200)

class ProblemPublicViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemPublicViewTests, self).setUp()
        self.test_moderated_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                                     'moderated': Problem.MODERATED,
                                                                     'publication_status': Problem.PUBLISHED})
        self.test_unmoderated_problem = create_test_instance(Problem, {'organisation': self.test_organisation})
        self.test_private_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                                   'public':False,
                                                                   'public_reporter_name':False,
                                                                   'moderated': Problem.MODERATED,
                                                                   'publication_status': Problem.PUBLISHED})

        self.test_moderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_moderated_problem.id,
                                                                            'cobrand':'choices'})
        self.test_unmoderated_problem_url = reverse('problem-view', kwargs={'pk': self.test_unmoderated_problem.id,
                                                                              'cobrand':'choices'})
        self.test_private_problem_url = reverse('problem-view', kwargs={'pk': self.test_private_problem.id,
                                                                          'cobrand':'choices'})

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

    def test_private_problem_accessible_to_allowed_user(self):
        self.login_as(self.provider)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.other_provider)
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

    def test_unmoderated_problem_accessible_to_allowed_user(self):
        self.login_as(self.provider)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.other_provider)
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

class ProblemProviderPickerTests(TestCase):

    def setUp(self):
        pick_provider_url = reverse('problems-pick-provider', kwargs={'cobrand':'choices'})
        self.results_url = "{0}?organisation_type={1}&location={2}".format(pick_provider_url, 'gppractices', 'London')

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

class ProblemSurveyTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemSurveyTests, self).setUp()
        self.test_problem = create_test_instance(Problem, {'organisation':self.test_organisation})
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
        resp = self.client.get(self.form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_service, False)

    def test_form_page_records_the_happy_service_yes_response(self):
        form_page = reverse('survey-form', kwargs={'cobrand': 'choices',
                                                   'response': 'y',
                                                   'id': int_to_base32(self.test_problem.id),
                                                   'token': self.test_problem.make_token(5555)})
        self.assertEqual(self.test_problem.happy_service, None)
        resp = self.client.get(form_page)
        test_problem = Problem.objects.get(id=self.test_problem.id)
        self.assertEqual(test_problem.happy_service, True)
