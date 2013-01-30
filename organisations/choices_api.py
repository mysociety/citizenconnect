# Standard imports
import urllib
from xml.dom import minidom

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
        xmldoc = minidom.parse(document)
        results = xmldoc.getElementsByTagName("entry")
        return results
