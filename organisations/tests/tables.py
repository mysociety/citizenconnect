# encoding: utf-8

from django.test import TestCase

from issues.models import Problem
from ..tables import ProblemTable
from .lib import create_test_organisation, create_test_problem

class ProblemTableTest(TestCase):
    def setUp(self):
        self.organisation = create_test_organisation()
        problem_attributes = {'description': "<script>alert('xss')</script>",
                              'organisation': self.organisation,
                              'publication_status': Problem.PUBLISHED,
                              'moderated_description': "<script>alert('xss')</script>"}
        self.problem = create_test_problem(problem_attributes)

    def test_escaping_private_summary(self):
        table = ProblemTable([], private=True)
        link = table.render_summary_as_response_link(self.problem)
        expected = '<a href="/private/response/{0}">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;'.format(self.problem.id)
        self.assertEqual(link, expected)

    def test_escaping_public_record_summary(self):
        table = ProblemTable([], private=False, cobrand='choices')
        link = table.render_summary_as_public_link(self.problem)
        expected = '<a href="/choices/problem/{0}">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;'.format(self.problem.id)
        self.assertEqual(link, expected)

    def test_escaping_summary(self):
        table = ProblemTable([], private=False, cobrand='choices')
        self.problem.public = False
        link = table.render_summary(self.problem)
        expected = 'Private'
        self.assertEqual(link, expected)
