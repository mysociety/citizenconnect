# Standard imports
import urllib
import urllib2
import xml.etree.ElementTree as ET
import os
import logging

# Django imports
from django.conf import settings

logger = logging.getLogger(__name__)


class ChoicesAPI():


    def __init__(self):
        self.atom_namespace = '{http://www.w3.org/2005/Atom}'
        self.services_namespace = '{http://syndication.nhschoices.nhs.uk/services}'
        self.syndication_namespace = '{http://schemas.datacontract.org/2004/07/NHSChoices.Syndication.Resources}'
        self.organisation_namespace = '{http://schemas.datacontract.org/2004/07/NHSChoices.Syndication.Resources.Orgs}'

    def search_types(self):
        return ['postcode', 'name', 'all']

    def example_hospitals(self):
        example_data = open(os.path.join(settings.PROJECT_ROOT, 'organisations', 'fixtures', 'SW1A1AA.xml'))
        organisations = self.parse_organisations(example_data, 'hospitals')
        return organisations

    def construct_url(self, path_elements, parameters={}):
        parameters['apikey'] = settings.NHS_CHOICES_API_KEY
        path = '/'.join(path_elements)
        querystring = urllib.urlencode(parameters)
        url = "%(base_url)s%(path)s?%(querystring)s" % {'path': path,
                                                        'querystring': querystring,
                                                        'base_url': settings.NHS_CHOICES_BASE_URL}
        return url

    def send_api_request(self, url):
        """Send a request to the API, return response object. Adds user agent."""
        user_agent = "CitizenConnect ChoicesAPI"

        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', user_agent)]
        response = opener.open(url)

        return response

    def _query_api(self, path_elements, parameters):
        url = self.construct_url(path_elements, parameters)
        return self.send_api_request(url)

    def find_all_organisations(self, search_type, search_value=None):
        """
        Find all the organisations in the choices api for a given search
        """
        if search_type not in self.search_types():
            raise ValueError("Unknown search type: %s" % (search_type))

        organisations = []

        for organisation_type in settings.ORGANISATION_TYPES:
            results = self.find_organisations(organisation_type, search_type, search_value)
            organisations.extend(results)

        return organisations

    def find_organisations(self, organisation_type, search_type, search_value=None):

        if search_type not in self.search_types():
            raise ValueError("Unknown search type: %s" % (search_type))
        if organisation_type not in settings.ORGANISATION_TYPES:
            raise ValueError("Unknown organisation type: %s" % (organisation_type))
        path_elements = ['organisations',
                         organisation_type,
                         search_type]
        if search_value:
            path_elements.append(search_value)
        # Add the format suffix to the last path element
        path_elements[-1] = path_elements[-1] + '.xml'
        parameters = {}
        if search_type == 'postcode':
            parameters['range'] = 5
        data = self._query_api(path_elements, parameters)
        return self.parse_organisations(data, organisation_type)

    def get_organisation_name(self, organisation_type, choices_id):
        path_elements = ['organisations',
                         organisation_type,
                         choices_id + '.xml']
        data = self._query_api(path_elements, {})
        organisation = self.parse_organisation(data)
        return organisation['name']

    def get_organisation_services(self, organisation_type, choices_id):
        path_elements = ['organisations',
                         organisation_type,
                         choices_id,
                         'services.xml']
        data = self._query_api(path_elements, {})
        return self.parse_services(data)

    def get_organisation_recommendation_rating(self, organisation_type, choices_id):
        path_elements = ['organisations',
                         organisation_type,
                         str(choices_id) + '.xml']
        try:
            data = self._query_api(path_elements, {})
            organisation = self.parse_organisation(data)
            return organisation['rating']
        except urllib2.HTTPError as e:
            if e.code == 404:
                # The Choices API returns a 404 when there are no ratings for
                # and organisation, this is ok
                return None
            else:
                raise(e)

    def parse_services(self, document):
        services = []
        # TODO: error handling
        tree = ET.parse(document)
        for entry_element in tree.getiterator('%sentry' % self.atom_namespace):
            service = {}
            content = entry_element.find('%scontent' % self.atom_namespace)
            # print content
            service_element = content.find('%sservicesummary' % self.services_namespace)
            type_element = service_element.find('%stype' % self.services_namespace)
            service['name'] = type_element.text
            service['service_code'] = type_element.attrib['code']
            services.append(service)

        return services

    def parse_organisations(self, document, organisation_type):
        organisations = []

        # TODO: error handling
        tree = ET.parse(document)
        for entry_element in tree.getiterator('%sentry' % self.atom_namespace):
            organisation = {}
            identifier = entry_element.find('%sid' % self.atom_namespace).text
            organisation['choices_id'] = identifier.split('/')[-1]
            content = entry_element.find('%scontent' % self.atom_namespace)
            summary = content.find('%sorganisationSummary' % self.services_namespace)
            organisation['name'] = summary.find('%sname' % self.services_namespace).text
            organisation['ods_code'] = None
            ods_variants = ['odscode', 'odsCode']
            for ods_variant in ods_variants:
                ods_element = summary.find('%s%s' % (self.services_namespace, ods_variant))
                if ods_element is not None:
                    organisation['ods_code'] = ods_element.text
            organisation['organisation_type'] = organisation_type
            coordinates = summary.find('%sgeographicCoordinates' % self.services_namespace)
            lon = float(coordinates.find('%slongitude' % self.services_namespace).text)
            lat = float(coordinates.find('%slatitude' % self.services_namespace).text)
            organisation['coordinates'] = {'lon': lon, 'lat': lat}
            # alternate_link = entry_element.find("%slink[@rel='alternate']" % self.atom_namespace)
            # organisation['choices_review_url'] = alternate_link.attr['href']
            organisations.append(organisation)

        return organisations

    def parse_organisation(self, document):
        organisation_dict = {}

        # TODO: error handling
        tree = ET.parse(document)
        organisation = tree.getroot()

        # Name
        link = organisation.find('%sLink' % self.syndication_namespace)
        text = link.find('%sText' % self.syndication_namespace)
        organisation_dict['name'] = text.text

        # FiveStarRecommendationRating (aka: Friends and Family recommendation)
        # A number between 1 and 5
        organisation_dict['rating'] = None
        five_star_rating = organisation.find('%sFiveStarRecommendationRating' % self.organisation_namespace)
        if five_star_rating is not None:
            try:
                rating = five_star_rating.find('%sValue' % self.organisation_namespace)
                if rating is not None:
                    organisation_dict['rating'] = float(rating.text)
            except (AttributeError, ValueError):
                # Probably an empty string or it doesn't have a five star
                # recommendation rating element at all - ignore it
                pass

        return organisation_dict
