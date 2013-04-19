# encoding: utf-8

from django.test import TestCase

from issues.models import Problem
from ..tables import ProblemTable
from .lib import create_test_organisation, create_test_instance

class ProblemTableTest(TestCase):
    def setUp(self):
        self.organisation = create_test_organisation()
        problem_attributes = {'description': "<script>alert('xss')</script>",
                              'organisation': self.organisation,
                              'publication_status': Problem.PUBLISHED,
                              'moderated_description': "<script>alert('xss')</script>"}
        self.problem = create_test_instance(Problem, problem_attributes)

    def test_escaping_private_summary(self):
        table = ProblemTable([], private=True)
        link = table.render_summary_as_response_link(self.problem)
        self.assertEqual(link, '<a href="/private/response/1">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;')
