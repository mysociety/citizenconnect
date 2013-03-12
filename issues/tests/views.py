from django.test import TestCase

from organisations.tests import create_test_instance, create_test_organisation, AuthorizationTestCase
from responses.models import QuestionResponse, ProblemResponse

from ..models import Question, Problem, MessageModel

class AskQuestionViewTests(TestCase):
    def setUp(self):
        self.url = '/choices/question/ask-question'

    def test_ask_question_page_exists(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_ask_question_page_links_to_question_form(self):
        resp = self.client.get(self.url)
        self.assertContains(resp, '/choices/question/question-form')

class QuestionPublicViewTests(TestCase):

    def setUp(self):
        self.test_question = Question(description='A Test Question',
                                    category='general',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
                                    public=True,
                                    public_reporter_name=True,
                                    preferred_contact_method=Question.CONTACT_EMAIL,
                                    status=Question.NEW)
        self.test_question.save()

    def test_public_question_page_exists(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_question_displays_responses(self):
        response1 = QuestionResponse.objects.create(response="response 1", message=self.test_question)
        response2 = QuestionResponse.objects.create(response="response 2", message=self.test_question)
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_question_displays_empty_response_message(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, "No responses", count=1, status_code=200)

class ProblemPublicViewTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemPublicViewTests, self).setUp()
        self.test_moderated_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                                     'moderated': MessageModel.MODERATED,
                                                                     'publication_status': MessageModel.PUBLISHED})
        self.test_unmoderated_problem = create_test_instance(Problem, {'organisation': self.test_organisation})
        self.test_private_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                                   'public':False,
                                                                   'public_reporter_name':False,
                                                                   'moderated': MessageModel.MODERATED,
                                                                   'publication_status': MessageModel.PUBLISHED})

        self.test_moderated_problem_url = '/choices/problem/{0}'.format(self.test_moderated_problem.id)
        self.test_unmoderated_problem_url = '/choices/problem/{0}'.format(self.test_unmoderated_problem.id)
        self.test_private_problem_url = '/choices/problem/{0}'.format(self.test_private_problem.id)

    def test_public_problem_page_exists(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, self.test_organisation.name, count=2, status_code=200)

    def test_public_problem_displays_responses(self):
        response1 = ProblemResponse.objects.create(response="response 1", message=self.test_moderated_problem)
        response2 = ProblemResponse.objects.create(response="response 2", message=self.test_moderated_problem)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, response1.response, count=1, status_code=200)
        self.assertContains(resp, response2.response, count=1, status_code=200)

    def test_public_problem_displays_empty_response_message(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertContains(resp, "No responses", count=1, status_code=200)

    def test_public_problem_accessible_to_everyone(self):
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.test_allowed_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.superuser)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

        self.login_as(self.test_other_provider_user)
        resp = self.client.get(self.test_moderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_allowed_user(self):
        self.login_as(self.test_allowed_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_private_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.test_other_provider_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_private_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_private_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_private_problem_accessible_to_pals_user(self):
        self.login_as(self.test_pals_user)
        resp = self.client.get(self.test_private_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_accessible_to_allowed_user(self):
        self.login_as(self.test_allowed_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_inaccessible_to_other_provider_user(self):
        self.login_as(self.test_other_provider_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 403)

    def test_unmoderated_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            resp = self.client.get(self.test_unmoderated_problem_url)
            self.assertEqual(resp.status_code, 200)

    def test_unmoderated_problem_accessible_to_pals_user(self):
        self.login_as(self.test_pals_user)
        resp = self.client.get(self.test_unmoderated_problem_url)
        self.assertEqual(resp.status_code, 200)

class ProblemProviderPickerTests(TestCase):

    def setUp(self):
        self.results_url = "/choices/problem/pick-provider?organisation_type=gppractices&location=London"

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

