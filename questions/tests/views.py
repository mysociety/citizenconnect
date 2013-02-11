from django.test import TestCase

from organisations.tests import MockedChoicesAPITest, create_test_instance

from ..models import Question

class PublicViewTests(MockedChoicesAPITest):

    def setUp(self):
        super(PublicViewTests, self).setUp()
        self.test_question = create_test_instance(Question, {})

    def test_public_question_page_exists(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_question_displays_organisation_name(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, 'Test Organisation Name', count=1, status_code=200)
