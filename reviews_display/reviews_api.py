import logging
import re

from HTMLParser import HTMLParser
import lxml.etree as ET

import urllib
from furl import furl

from organisations.choices_api import ChoicesAPI

logger = logging.getLogger(__name__)


class ReviewsAPI(object):

    """
    Abstraction around the Choices API that hides the pagination and parsing
    of the XML and lets us use an iterator to access the reviews.
    """

    def __init__(self, organisation_type, start_page=None, max_fetch=5, since=None):
        self.api = ChoicesAPI()

        self.organisation_type = organisation_type

        self.fetches_remaining = max_fetch

        # create the start page if not specified
        if not start_page:

            path_elements = [
                'organisations',
                self.organisation_type,
            ]

            if since:
                path_elements.append('commentssince')
                path_elements.extend(
                    map(str, [since.year, since.month, since.day])
                )
            else:
                path_elements.append('comments')

            # add '.atom' so we get a consistent format, which includes ratings
            path_elements[-1] += ".atom"

            start_page = self.api.construct_url(path_elements)

        self.next_page_url = start_page
        self.reviews = []

    def __iter__(self):
        return self

    def next(self):

        if not len(self.reviews):
            self.load_next_page()

        try:
            return self.reviews.pop(0)
        except IndexError:
            raise StopIteration

    def fetch_from_api(self, url):

        # Check that we can fetch more
        if not self.fetches_remaining:
            return None
        self.fetches_remaining -= 1

        logger.debug("Fetching '%s'" % url)
        response = urllib.urlopen(url)

        if response.getcode() == 404:
            # They use 404 for empty responses :(
            return None

        data = response.read()
        data = self.cleanup_xml(data)
        return data

    def cleanup_xml(self, xml):
        """
        There does not appear to be a way to tell ElementTree to ignore the
        namespaces. Use a regex to fix the raw XML string.
        """
        xml = re.sub(r'xmlns=".*?"', '', xml)

        # xml = xml.decode('utf8')

        return xml

    def _extract_content(self, element):
        if element is None: return ""
        content = ET.tostring(element, method="text", encoding='utf8')
        content = content.decode('utf8')
        content = content or ""
        content = HTMLParser().unescape(content)
        return content

    def convert_entry_to_review(self, entry):

        review = {
            "api_posting_id": entry.find('id').text,
            "api_postingorganisationid": entry.find('postingorganisationid').text,

            "api_published": entry.find("published").text,
            "api_updated": entry.find("updated").text,

            "api_category": entry.find("category").get("term"),

            "author_display_name": entry.find("author/name").text,
            "title":   HTMLParser().unescape(entry.find('title').text or ""),
        }

        # Extract the content so that we can manipulate it a bit
        content_xml = entry.find('content')

        if review['api_category'] == 'comment':


            # For comments there are nested divs. Remove them, but make sure
            # to put '\n\n' between their content so that they are not just
            # pushed together.
            review['content_liked'] = self._extract_content(content_xml.find('div[@id="liked"]'))
            review['content_improved'] = self._extract_content(content_xml.find('div[@id="improved"]'))
            review['content'] = self._extract_content(content_xml.find('div[@id="anythingElse"]'))
        else:
            review['content_liked'] = ''
            review['content_improved'] = ''
            review['content'] = self._extract_content(content_xml)

        # for replies we should extract what it is a reply to
        if review['api_category'] == 'reply':
            review["in_reply_to_id"] = entry.find("in-reply-to").get("ref")
        else:
            review["in_reply_to_id"] = None

        # get the organisation
        org_url = entry.find(
            'link[@title="Organisation commented on"]').get('href')

        review['organisation_choices_id'] = re.search(
            r'/(\d+)\?', org_url).group(1)

        review["ratings"] = []
        for rating in entry.iter("rating"):
            review['ratings'].append({
                "question": rating.find("questionText").text,
                "answer": rating.find("answerText").text,
                "score": rating.find("answerMetric").get('value'),
            })

        return review

    def extract_reviews_from_xml(self, xml):

        # for 404 responses
        if xml is None:
            return []

        root = ET.fromstring(xml)
        reviews = []
        for entry in root.iter('entry'):
            review = self.convert_entry_to_review(entry)
            reviews.append(review)
        return reviews

    def extract_next_page_url(self, xml):

        # for 404 responses
        if xml is None:
            return None

        root = ET.fromstring(xml)
        next_page_url = root.find('link[@rel="next"]').get('href')
        last_page_url = root.find('link[@rel="last"]').get('href')

        if next_page_url == last_page_url:
            return None

        # parse the url and check that the path ends with '.atom'. Add it if
        # missing.
        url = furl(next_page_url)
        if not re.search(r'\.atom$', str(url.path)):
            url.path = str(url.path) + '.atom'
            next_page_url = str(url)

        return next_page_url

    def load_next_page(self):

        if not self.next_page_url:
            return None

        xml = self.fetch_from_api(self.next_page_url)

        # error with fetching, or have fetched up to our limit
        if not xml:
            self.next_page_url = None
            return None

        reviews_from_xml = self.extract_reviews_from_xml(xml)
        self.reviews.extend(reviews_from_xml)

        self.next_page_url = self.extract_next_page_url(xml)

        return None
