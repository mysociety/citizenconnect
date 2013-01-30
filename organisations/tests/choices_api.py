# Standard imports
import os.path

# Django imports
from django.test import TestCase

# App imports
import organisations
from organisations.choices_api import ChoicesAPI


class ChoicesAPITests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])

    def test_parses_correct_number_of_results_from_example_file(self):
        """
        Tests that parse_organisations correctly parses an example file
        """
        api = ChoicesAPI()
        example_data = open(os.path.join(self._organisations_path, 'fixtures', 'SW1A1AA.xml'))
        results = api.parse_organisations(example_data)
        self.assertEqual(len(results), 10)
