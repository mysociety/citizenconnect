# encoding: utf-8

from django.test import TestCase

from issues.models import Problem
from ..tables import ProblemTable
from .lib import create_test_organisation, create_test_instance

class ProblemTableTest(TestCase):
    def setUp(self):
        self.organisation = create_test_organisation()
        problem_attributes = {'description': "<script>alert('xss')</script>",
                              'organisation': self.organisation}
        self.problem = create_test_instance(Problem, problem_attributes)
