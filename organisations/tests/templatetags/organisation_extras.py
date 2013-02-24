# Django imports
from django.test import TestCase
from ...templatetags.organisation_extras import true_to_false_percent

class TrueToFalsePercentTests(TestCase):

    def test_formats_simple_case_correctly(self):
        attributes = {'success_true': 3, 'success_false': 3}
        formatted_percent = true_to_false_percent(attributes, 'success')
        self.assertEqual(formatted_percent, '50%')

    def test_rounds_results_to_nearest_percent(self):
        attributes = {'success_true': 1, 'success_false': 2}
        formatted_percent = true_to_false_percent(attributes, 'success')
        self.assertEqual(formatted_percent, '33%')

    def test_returns_dash_for_divide_by_zero(self):
        attributes = {'success_true': 0, 'success_false': 0}
        formatted_percent = true_to_false_percent(attributes, 'success')
        self.assertEqual(formatted_percent, '-')
