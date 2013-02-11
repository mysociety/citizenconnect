from django.test import TestCase

from organisations.tests import MockedChoicesAPITest, create_test_instance

from ..models import Problem

class PublicViewTests(MockedChoicesAPITest):

    def setUp(self):
        super(PublicViewTests, self).setUp()
        self.test_problem = create_test_instance(Problem, {})

    def test_public_problem_page_exists(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, 'Test Organisation Name', count=1, status_code=200)
