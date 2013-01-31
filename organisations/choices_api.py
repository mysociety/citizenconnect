# Standard imports
import urllib
import xml.etree.ElementTree as ET
import os

# Django imports
from django.conf import settings


class ChoicesAPI():

    def search_types(self):
        return ['postcode', 'name']

    def organisation_types(self):
        return ['hospitals', 'gppractices']

    def example_hospitals(self):
        example_data = open(os.path.join(settings.PROJECT_ROOT, 'organisations', 'fixtures', 'SW1A1AA.xml'))
        organisations = self.parse_organisations(example_data)
        return organisations

    def find_organisations(self, search_type, search_value, organisation_type):
        if search_type not in self.search_types():
            raise ValueError("Unknown search type: %s" % (search_type))
        if organisation_type not in self.organisation_types():
            raise ValueError("Unknown organisation type: %s" % (organisation_type))

        path_elements = ['organisations',
                         organisation_type,
                         search_type,
                         search_value + '.xml']
        path = '/'.join(path_elements)

        parameters = {'apikey': settings.NHS_CHOICES_API_KEY}
        if search_type == 'postcode':
            parameters['range'] = 5
        querystring = urllib.urlencode(parameters)
        url = "%(base_url)s%(path)s?%(querystring)s" % {'path' : path,
                                                        'querystring': querystring,
                                                        'base_url': settings.NHS_CHOICES_BASE_URL}
        organisations = self.parse_organisations(urllib.urlopen(url))
        return organisations

    def parse_organisations(self, document):
        tree = ET.parse(document)
        organisations = []

        for entry_element in tree.getiterator('{http://www.w3.org/2005/Atom}entry'):
            organisation = {}
            organisation['id'] = entry_element.find('{http://www.w3.org/2005/Atom}id').text
            content = entry_element.find('{http://www.w3.org/2005/Atom}content')
            summary = content.find("{http://syndication.nhschoices.nhs.uk/services}organisationSummary")
            organisation['name'] = summary.find('{http://syndication.nhschoices.nhs.uk/services}name').text
            organisations.append(organisation)
        return organisations
