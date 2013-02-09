# Standard imports
import urllib
import xml.etree.ElementTree as ET
import os

# Django imports
from django.conf import settings


class ChoicesAPI():

    def __init__(self):
        self.atom_namespace = '{http://www.w3.org/2005/Atom}'
        self.services_namespace = '{http://syndication.nhschoices.nhs.uk/services}'
        self.syndication_namespace = '{http://schemas.datacontract.org/2004/07/NHSChoices.Syndication.Resources}'

    def search_types(self):
        return ['postcode', 'name']

    def organisation_types(self):
        return ['hospitals', 'gppractices']

    def example_hospitals(self):
        example_data = open(os.path.join(settings.PROJECT_ROOT, 'organisations', 'fixtures', 'SW1A1AA.xml'))
        organisations = self.parse_organisations(example_data, 'hospitals')
        return organisations

    def _query_api(self, path_elements, parameters):
        parameters['apikey'] = settings.NHS_CHOICES_API_KEY
        path = '/'.join(path_elements)
        querystring = urllib.urlencode(parameters)
        url = "%(base_url)s%(path)s?%(querystring)s" % {'path' : path,
                                                        'querystring': querystring,
                                                        'base_url': settings.NHS_CHOICES_BASE_URL}
        return urllib.urlopen(url)

    def find_organisations(self, search_type, search_value, organisation_type):
        if search_type not in self.search_types():
            raise ValueError("Unknown search type: %s" % (search_type))
        if organisation_type not in self.organisation_types():
            raise ValueError("Unknown organisation type: %s" % (organisation_type))
        path_elements = ['organisations',
                         organisation_type,
                         search_type,
                         search_value + '.xml']
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
        return self.parse_organisation(data)

    def get_organisation_services(self, organisation_type, choices_id):
        path_elements = ['organisations',
                         organisation_type,
                         choices_id,
                         'services.xml']
        data = self._query_api(path_elements, {})
        return self.parse_services(data)

    def parse_organisations(self, document, organisation_type):
        tree = ET.parse(document)
        organisations = []

        for entry_element in tree.getiterator('%sentry' % self.atom_namespace):
            organisation = {}
            identifier = entry_element.find('%sid' % self.atom_namespace).text
            organisation['choices_id'] = identifier.split('/')[-1]
            content = entry_element.find('%scontent' % self.atom_namespace)
            summary = content.find('%sorganisationSummary' % self.services_namespace)
            organisation['name'] = summary.find('%sname' % self.services_namespace).text
            ods_element = summary.find('%sodsCode' % self.services_namespace)
            if ods_element != None:
                organisation['ods_code'] = ods_element.text
            else:
                organisation['ods_code'] = None
            organisation['organisation_type'] = organisation_type
            coordinates = summary.find('%sgeographicCoordinates' % self.services_namespace)
            lon = float(coordinates.find('%slongitude' % self.services_namespace).text)
            lat = float(coordinates.find('%slatitude' % self.services_namespace).text)
            organisation['coordinates'] = {'lon':lon, 'lat':lat}
            organisations.append(organisation)
        return organisations

    def parse_organisation(self, document):
        tree = ET.parse(document)
        organisation = tree.getroot()
        link = organisation.find('%sLink' % self.syndication_namespace)
        text = link.find('%sText' % self.syndication_namespace)
        return text.text
