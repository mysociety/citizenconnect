from django.test import TestCase

from organisations.tests import create_test_instance, create_test_organisation

from ..models import Problem

class PublicViewTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_instance(Problem, {'organisation': self.test_organisation})

    def test_public_problem_page_exists(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, self.test_organisation.name, count=1, status_code=200)
