# encoding: utf-8

from django.test import TestCase
from django.core.urlresolvers import reverse

from organisations.tests.lib import create_test_organisation, create_test_problem

from ..models import Problem
from ..tables import ProblemTable


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
        response_url = reverse('response-form', kwargs={'pk': self.problem.id})
        expected = '<a href="{0}">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt; <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(response_url)
        self.assertEqual(link, expected)

    def test_escaping_public_record_summary(self):
        table = ProblemTable([], private=False, cobrand='choices')
        link = table.render_summary_as_public_link(self.problem)
        problem_url = reverse('problem-view', kwargs={'pk': self.problem.id, 'cobrand': 'choices'})
        expected = '<a href="{0}">&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;</a>'.format(problem_url)
        self.assertEqual(link, expected)

    def test_escaping_summary(self):
        table = ProblemTable([], private=False, cobrand='choices')
        self.problem.public = False
        link = table.render_summary(self.problem)
        expected = 'Private'
        self.assertEqual(link, expected)
