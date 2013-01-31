# Standard imports
import os.path
from mock import MagicMock
import urllib

# Django imports
from django.test import TestCase

# App imports
import organisations
from organisations.choices_api import ChoicesAPI


class ChoicesAPIExampleFileTests(TestCase):

    # Use a fixture file to mock the contents of the API url
    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])
        cls._api = ChoicesAPI()
        cls._example_data = open(os.path.join(cls._organisations_path, 'fixtures', 'SW1A1AA.xml'))
        urllib.urlopen = MagicMock(return_value=cls._example_data)

    # Reset the fixture file so that we can read it again
    def tearDown(self):
        self._example_data.seek(0)

    # Close the fixture file
    @classmethod
    def tearDownClass(cls):
        cls._example_data.close()

    def parse_example_file(self):
        results = self._api.parse_organisations(self._example_data)
        return results

    def test_parses_correct_number_of_results(self):
        """
        Tests that parse_organisations correctly parses an example file
        """
        results = self.parse_example_file()
        self.assertEqual(len(results), 10)

    def test_parses_organisation_names(self):
        results = self._api.parse_organisations(self._example_data)
        self.assertEqual(results[0]['name'], 'The Gordon Hospital')
        self.assertEqual(results[-1]['name'], 'Western Eye Hospital')

    def test_parses_organisation_ids(self):
        results = self.parse_example_file()
        first_expected_id = 'http://v1.syndication.nhschoices.nhs.uk/organisations/hospitals/42192'
        last_expected_id = 'http://v1.syndication.nhschoices.nhs.uk/organisations/hospitals/43804'
        self.assertEqual(results[0]['id'], first_expected_id)
        self.assertEqual(results[-1]['id'], last_expected_id)

    def test_handles_unknown_search_type(self):
        with self.assertRaises(ValueError) as context_manager:
            self._api.find_organisations('sometype', 'value', 'hospitals')
        exception = context_manager.exception
        self.assertEqual(str(exception), 'Unknown search type: sometype')

    def test_handles_unknown_provider_type(self):
        with self.assertRaises(ValueError) as context_manager:
            self._api.find_organisations('name', 'value', 'someprovider')
        exception = context_manager.exception
        self.assertEqual(str(exception), 'Unknown organisation type: someprovider')

    def test_generates_api_url(self):
        self._api.find_organisations('postcode', 'SW1A', 'gppractices')
        expected = 'http://v1.syndication.nhschoices.nhs.uk/organisations/gppractices/postcode/SW1A.xml?range=5&apikey=OURKEY'
        urllib.urlopen.assert_called_once_with(expected)
