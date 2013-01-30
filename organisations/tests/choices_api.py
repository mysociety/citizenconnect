# Standard imports
import os.path

# Django imports
from django.test import TestCase

# App imports
import organisations
from organisations.choices_api import ChoicesAPI


class ChoicesAPIExampleFileTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])
        cls._api = ChoicesAPI()

    def parse_example_file(self, filename):
        example_data = open(os.path.join(self._organisations_path, 'fixtures', filename))
        results = self._api.parse_organisations(example_data)
        return results

    def test_parses_correct_number_of_results(self):
        """
        Tests that parse_organisations correctly parses an example file
        """
        results = self.parse_example_file('SW1A1AA.xml')
        self.assertEqual(len(results), 10)

    def test_parses_organisation_names(self):
        results = self.parse_example_file('SW1A1AA.xml')
        self.assertEqual(results[0]['name'], 'The Gordon Hospital')
        self.assertEqual(results[-1]['name'], 'Western Eye Hospital')

    def test_parses_organisation_ids(self):
        results = self.parse_example_file('SW1A1AA.xml')
        first_expected_id = 'http://v1.syndication.nhschoices.nhs.uk/organisations/hospitals/42192'
        last_expected_id = 'http://v1.syndication.nhschoices.nhs.uk/organisations/hospitals/43804'
        self.assertEqual(results[0]['id'], first_expected_id)
        self.assertEqual(results[-1]['id'], last_expected_id)


