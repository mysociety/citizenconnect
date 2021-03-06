# Standard imports
import os.path
import urllib2
from mock import Mock, MagicMock

# Django imports
from django.test import TestCase
from django.conf import settings
from django.test.utils import override_settings

# App imports
import organisations
from organisations.choices_api import ChoicesAPI


# A test case that uses a fixture file to mock the contents of the API urlopen call
class ExampleFileAPITest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._organisations_path = os.path.abspath(organisations.__path__[0])
        cls._example_data = open(os.path.join(cls._organisations_path,
                                              'fixtures',
                                              'choices_api',
                                              cls._example_file))

    def setUp(self):
        # Reset the api in case we modify it inside tests
        self._api = ChoicesAPI()
        self._original_send_api_request = ChoicesAPI.send_api_request
        ChoicesAPI.send_api_request = MagicMock(return_value=self._example_data)

    # Reset the fixture file so that we can read it again
    def tearDown(self):
        self._example_data.seek(0)
        ChoicesAPI.send_api_request = self._original_send_api_request

    # Close the fixture file
    @classmethod
    def tearDownClass(cls):
        cls._example_data.close()


class ChoicesAPIOrganisationsSearchResultExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        cls._example_file = 'SW1A1AA.xml'
        super(ChoicesAPIOrganisationsSearchResultExampleFileTests, cls).setUpClass()

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
            'lon': -0.137492403388023,
            'lat': 51.4915466308594
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

    @override_settings(NHS_CHOICES_API_KEY='OURKEY')
    def test_generates_api_url_for_postcode(self):
        self._api.find_organisations('gppractices', 'postcode', 'SW1A')
        expected = '{0}organisations/gppractices/postcode/SW1A.xml?range=5&apikey=OURKEY'.format(settings.NHS_CHOICES_BASE_URL)
        ChoicesAPI.send_api_request.assert_called_once_with(expected)

    @override_settings(NHS_CHOICES_API_KEY='OURKEY')
    def test_generates_api_url_for_all(self):
        self._api.find_organisations('gppractices', 'all')
        expected = '{0}organisations/gppractices/all.xml?apikey=OURKEY'.format(settings.NHS_CHOICES_BASE_URL)
        ChoicesAPI.send_api_request.assert_called_once_with(expected)

    def test_finds_all_organisations(self):
        # Mock find_organisations to return a dummy result
        self._api.find_organisations = MagicMock(return_value=[{'name': 'Test Organisation'}])
        # We expect it to be called once for each organisation type
        expected_number_of_results = len(settings.ORGANISATION_TYPES)
        organisations = self._api.find_all_organisations("postcode", "SW1A1AA")
        self.assertEqual(len(organisations), expected_number_of_results)


class ChoicesAPIOrganisationsAllResultExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        # Fixture for a particular organisation
        cls._example_file = 'gp_all_page.xml'
        super(ChoicesAPIOrganisationsAllResultExampleFileTests, cls).setUpClass()

    # ODS codes in a different format
    def test_parses_ods_codes(self):
        results = self._api.parse_organisations(self._example_data, 'gppractices')
        first_expected_id = 'M85174'
        last_expected_id = 'D81035'
        self.assertEqual(results[0]['ods_code'], first_expected_id)
        self.assertEqual(results[-1]['ods_code'], last_expected_id)


class ChoicesAPIOneOrganisationExampleFileTests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        # Fixture for a particular organisation
        cls._example_file = '41265.xml'
        super(ChoicesAPIOneOrganisationExampleFileTests, cls).setUpClass()

    def test_parses_organisation_name(self):
        result = self._api.parse_organisation(self._example_data)
        self.assertEqual('Darent Valley Hospital', result['name'])

    def test_parses_recommendation_rating(self):
        result = self._api.parse_organisation(self._example_data)
        self.assertEqual(4.2857142857142856, result['rating'])


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


class ChoicesAPIErrorTests(TestCase):
    """Tests for when the choices API returns errors"""

    def setUp(self):
        # Reset the api in case we modify it inside tests
        self._api = ChoicesAPI()

    def test_get_organisation_recommendation_ratings_handles_404s(self):
        # We shouldn't raise 404 errors because they're expected and just mean
        # that there are no ratings for this organisation.
        not_found_error = urllib2.HTTPError("", 404, "", None, None)
        self._api.send_api_request = Mock(side_effect=not_found_error)

        self.assertEqual(
            self._api.get_organisation_recommendation_rating('hospitals', '12345'),
            None
        )

        # Other errors should come through though
        errors = (
            urllib2.URLError(""),
            urllib2.HTTPError("", 500, "", None, None),
            urllib2.HTTPError("", 403, "", None, None),
            KeyError(),
            ValueError()
        )
        for error in errors:
            self._api.send_api_request = Mock(side_effect=error)
            self.assertRaises(
                error.__class__,
                self._api.get_organisation_recommendation_rating,
                'hospitals',
                '12345'
            )
