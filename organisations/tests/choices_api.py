# Standard imports
import os.path
from mock import MagicMock, patch
import urllib

# Django imports
from django.test import TestCase
from django.conf import settings

# App imports
import organisations
from organisations.choices_api import ChoicesAPI

# A test case which will mock out the ChoicesAPI instance methods with some example values
class MockedChoicesAPITest(TestCase):

    def setUp(self):
        choices_api_patcher = patch('organisations.choices_api.ChoicesAPI')
        mock_api = choices_api_patcher.start()
        api_instance = mock_api.return_value
        # Mock the 'get_organisation_name' method of any API instances
        api_instance.get_organisation_name.return_value = 'Test Organisation Name'
        # Mock the 'find_all_organisations' method of any API Instances
        api_instance.find_all_organisations.return_value = [
            {
                "organisation_type": "hospitals",
                "name": "Test Hospital Name",
                "coordinates": {
                    "lat": 51.5197486877441, "lon": -0.0469740852713585
                },
                "choices_id": "18444",
            },
            {
                "organisation_type": "gppractices",
                "name": "Test GP Name",
                "coordinates": {
                    "lat": 51.5197486877441, "lon": -0.0469740852713585
                },
                "choices_id": "12702",
            }
        ]
        self.addCleanup(choices_api_patcher.stop)

# A test case that uses a fixture file to mock the contents of the API urlopen call
class ExampleFileAPITest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])
        cls._example_data = open(os.path.join(cls._organisations_path, 'fixtures', cls._example_file))
        urllib.urlopen = MagicMock(return_value=cls._example_data)
        cls._real_api_key = settings.NHS_CHOICES_API_KEY
        settings.NHS_CHOICES_API_KEY = 'OURKEY'

    def setUp(self):
        # Reset the api in case we modify it inside tests
        self._api = ChoicesAPI()

    # Reset the fixture file so that we can read it again
    def tearDown(self):
        self._example_data.seek(0)

    # Close the fixture file
    @classmethod
    def tearDownClass(cls):
        cls._example_data.close()
        settings.NHS_CHOICES_API_KEY = cls._real_api_key


class ChoicesAPIOrganisationsExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        cls._example_file = 'SW1A1AA.xml'
        super(ChoicesAPIOrganisationsExampleFileTests, cls).setUpClass()

    def parse_example_file(self, organisation_type):
        results = self._api.parse_organisations(self._example_data, organisation_type)
        return results

    def test_parses_correct_number_of_results(self):
        """
        Tests that parse_organisations correctly parses an example file
        """
        results = self.parse_example_file('hospitals')
        self.assertEqual(len(results), 10)

    def test_parses_organisation_names(self):
        results = self._api.parse_organisations(self._example_data, 'hospitals')
        self.assertEqual(results[0]['name'], 'The Gordon Hospital')
        self.assertEqual(results[-1]['name'], 'Western Eye Hospital')

    def test_parses_choices_ids(self):
        results = self.parse_example_file('hospitals')
        first_expected_id = '42192'
        last_expected_id = '43804'
        self.assertEqual(results[0]['choices_id'], first_expected_id)
        self.assertEqual(results[-1]['choices_id'], last_expected_id)

    def test_parses_ods_codes(self):
        results = self.parse_example_file('hospitals')
        first_expected_id = 'RV346'
        last_expected_id = 'RYJ07'
        self.assertEqual(results[0]['ods_code'], first_expected_id)
        self.assertEqual(results[-1]['ods_code'], last_expected_id)

    def test_parses_organisation_types(self):
        results = self.parse_example_file('hospitals')
        first_expected_type = 'hospitals'
        self.assertEqual(results[0]['organisation_type'], first_expected_type)

    def test_parses_coordinates(self):
        results = self.parse_example_file('hospitals')
        first_expected_coordinates = {
            'lon':-0.137492403388023,
            'lat':51.4915466308594
        }
        self.assertEqual(results[0]['coordinates'], first_expected_coordinates)

    def test_handles_unknown_search_type(self):
        with self.assertRaises(ValueError) as context_manager:
            self._api.find_organisations('hospitals', 'sometype', 'value')
        exception = context_manager.exception
        self.assertEqual(str(exception), 'Unknown search type: sometype')

    def test_handles_unknown_provider_type(self):
        with self.assertRaises(ValueError) as context_manager:
            self._api.find_organisations('someprovider', 'name', 'value')
        exception = context_manager.exception
        self.assertEqual(str(exception), 'Unknown organisation type: someprovider')

    def test_generates_api_url(self):
        self._api.find_organisations('gppractices', 'postcode', 'SW1A')
        expected = 'http://v1.syndication.nhschoices.nhs.uk/organisations/gppractices/postcode/SW1A.xml?range=5&apikey=OURKEY'
        urllib.urlopen.assert_called_once_with(expected)

    def test_finds_all_organisations(self):
        # Mock find_organisations to return a dummy result
        self._api.find_organisations = MagicMock(return_value=[{'name':'Test Organisation'}])
        # We expect it to be called once for each organisation type
        expected_number_of_results = len(settings.ORGANISATION_TYPES)
        organisations = self._api.find_all_organisations("postcode", "SW1A1AA")
        self.assertEqual(len(organisations), expected_number_of_results)

class ChoicesAPIOneOrganisationExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        # Fixture for a particular organisation
        cls._example_file = '41265.xml'
        super(ChoicesAPIOneOrganisationExampleFileTests, cls).setUpClass()

    def test_parses_organisation_name(self):
        result = self._api.parse_organisation(self._example_data)
        self.assertEqual('Darent Valley Hospital', result)

class ChoicesAPIOrganisationServicesExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        cls._example_file = 'services.xml'
        super(ChoicesAPIOrganisationServicesExampleFileTests, cls).setUpClass()

    def test_parses_correct_number_of_results(self):
        results = self._api.parse_services(self._example_data)
        self.assertEqual(3, len(results))

    def test_parses_service_ids(self):
        results = self._api.parse_services(self._example_data)
        first_expected = "SRV0017"
        last_expected = "SRV0046"
        self.assertEqual(first_expected, results[0]['service_code'])
        self.assertEqual(last_expected, results[-1]['service_code'])

    def test_parses_names(self):
        results = self._api.parse_services(self._example_data)
        first_expected = "Children's & Adolescent Services"
        last_expected = "Genetics"
        self.assertEqual(first_expected, results[0]['name'])
        self.assertEqual(last_expected, results[-1]['name'])
