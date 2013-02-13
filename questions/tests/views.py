from django.test import TestCase

from organisations.tests import MockedChoicesAPITest, create_test_instance, create_test_organisation

from ..models import Question

class PublicViewTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_question = create_test_instance(Question, {'organisation': self.test_organisation})

    def test_public_question_page_exists(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_question_displays_organisation_name(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, self.test_organisation.name, count=1, status_code=200)

class QuestionProviderPickerTests(MockedChoicesAPITest):

    def setUp(self):
        super(QuestionProviderPickerTests, self).setUp()
        self.results_url = "/choices/question/pick-provider?organisation_type=gppractices&location=London"

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

    def test_results_page_shows_organisations(self):
        resp = self.client.get(self.results_url)
        self.assertContains(resp, self.mock_gp_result['name'], count=1, status_code=200)
