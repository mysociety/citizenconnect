
from pprint import pprint
import re
from HTMLParser import HTMLParser
import xml.etree.ElementTree as ET

import urllib

from organisations.choices_api import ChoicesAPI


class ReviewsAPI(object):

    """
    Abstraction around the Choices API that hides the pagination and parsing
    of the XML and lets us use an iterator to access the reviews.
    """

    def __init__(self, organisation_type="hospitals", start_page=None, max_fetch=5):
        self.api = ChoicesAPI()

        self.organisation_type = organisation_type

        self.fetches_remaining = max_fetch

        # create the start page if not specified
        if not start_page:
            path_elements = [
                'organisations',
                self.organisation_type,
                'comments.atom'  # add '.atom' so we get a consistent format, which includes ratings
            ]
            start_page = self.api._construct_url(path_elements)

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

        data = urllib.urlopen(url).read()

        data = self.cleanup_xml(data)
        return data

    def cleanup_xml(self, xml):
        """
        There does not appear to be a way to tell ElementTree to ignore the
        namespaces. Use a regex to fix the raw XML string.
        """
        xml = re.sub(r'xmlns=".*?"', '', xml)
        return xml

    def convert_entry_to_review(self, entry):
        h = HTMLParser()

        review = {
            "api_posting_id": entry.find('id').text,
            "api_postingorganisationid": entry.find('postingorganisationid').text,

            "api_published": entry.find("published").text,
            "api_updated": entry.find("updated").text,

            "api_category": entry.find("category").get("term"),

            "author_display_name": entry.find("author/name").text,
            "title":   h.unescape(entry.find('title').text or ""),
            "content": h.unescape(entry.find('content').text or ""),
        }

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
        root = ET.fromstring(xml)
        reviews = []
        for entry in root.iter('entry'):
            review = self.convert_entry_to_review(entry)
            reviews.append(review)
        return reviews

    def extract_next_page_url(self, xml):
        root = ET.fromstring(xml)
        next_page_url = root.find('link[@rel="next"]').get('href')
        last_page_url = root.find('link[@rel="last"]').get('href')
        if next_page_url == last_page_url:
            next_page_url = None
        else:
            if not re.search(r'\.atom', next_page_url):
                next_page_url = re.sub(
                    r'comments', 'comments.atom', next_page_url)

        return next_page_url

    def load_next_page(self):

        if not self.next_page_url:
            return None

        xml = self.fetch_from_api(self.next_page_url)

        # error with fetching, or have fetched up to our limit
        if not xml:
            return None

        reviews_from_xml = self.extract_reviews_from_xml(xml)
        self.reviews.extend(reviews_from_xml)

        self.next_page_url = self.extract_next_page_url(xml)

        return None
