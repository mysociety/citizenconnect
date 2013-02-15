from django.test import TestCase

from organisations.tests import create_test_instance

from ..models import Problem

class ProblemModelTests(TestCase):

    def setUp(self):
        self.test_problem = create_test_instance(Problem, {})

    def test_has_prefix_property(self):
        self.assertEqual(Problem.PREFIX, 'P')
        self.assertEqual(self.test_problem.PREFIX, 'P')

    def test_has_reference_number_property(self):
        self.assertEqual(self.test_problem.reference_number, 'P{0}'.format(self.test_problem.id))