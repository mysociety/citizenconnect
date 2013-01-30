# Standard imports
import urllib
import xml.etree.ElementTree as ET

# Django imports
from django.conf import settings


class ChoicesAPI():

    def hospitals_by_postcode(self, postcode):
        base_url = settings.NHS_CHOICES_BASE_URL

        # organisation_type
        url = "%(base_url)sorganisations/hospitals/postcode/%(postcode)s.xml?apikey=%(apikey)s&range=5" % \
                {"base_url": settings.NHS_CHOICES_BASE_URL,
                 "postcode": postcode,
                 "apikey": settings.NHS_CHOICES_API_KEY}
        return urllib.urlopen(url)

    def parse_organisations(self, document):
        tree = ET.parse(document)
        organisations = []
        # print tree

        for entry_element in tree.getiterator('{http://www.w3.org/2005/Atom}entry'):
            organisation = {}
            organisation['id'] = entry_element.find('{http://www.w3.org/2005/Atom}id').text
            content = entry_element.find('{http://www.w3.org/2005/Atom}content')
            summary = content.find("{http://syndication.nhschoices.nhs.uk/services}organisationSummary")
            organisation['name'] = summary.find('{http://syndication.nhschoices.nhs.uk/services}name').text

            organisations.append(organisation)
        return organisations
