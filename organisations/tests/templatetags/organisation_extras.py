# Django imports
from django.test import TestCase
from ...templatetags.organisation_extras import percent

class TrueToFalsePercentTests(TestCase):

    def test_formats_simple_case_correctly(self):
        formatted_percent = percent(0.5)
        self.assertEqual(formatted_percent, '50%')

    def test_rounds_results_to_nearest_percent(self):
        formatted_percent = percent(0.33333333333333)
        self.assertEqual(formatted_percent, '33%')

    def test_returns_dash_for_divide_by_zero(self):
        formatted_percent = percent(None)
        self.assertEqual(formatted_percent, '-')
