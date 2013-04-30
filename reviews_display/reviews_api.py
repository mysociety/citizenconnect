
from organisations.choices_api import ChoicesAPI
from pprint import pprint
import re

import xml.etree.ElementTree as ET

import urllib

# TODO

# * stop at the last page
# * add in ratings


class ReviewsAPI(object):

    """
    Abstraction around the Choices API that hides the pagination and parsing
    of the XML and lets us use an iterator to access the reviews.
    """

    def __init__(self, organisation_type="hospitals"):
        self.api = ChoicesAPI()

        self.organisation_type = organisation_type

        self.next_page_url = None
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
        data = urllib.urlopen(url).read()

        # There does not appear to be a way to tell ElementTree to ignore the
        # namespaces. Use a regex to fix the raw XML string.
        data = re.sub(r'xmlns=".*?"', '', data)

        return data

    def load_next_page(self):

        # If we have a page then just return (deal with pagination later)
        if not self.next_page_url:
            # load the first page
            path_elements = [
                'organisations',
                self.organisation_type,
                'comments.atom'  # add '.atom' so we get a consistent format, which includes ratings
            ]
            url = self.api._construct_url(path_elements)
        else:
            url = self.next_page_url

        data = self.fetch_from_api(url)

        root = ET.fromstring(data)

        for entry in root.iter('entry'):

            review = {
                "api_posting_id": entry.find('id').text,
                "api_postingorganisationid": entry.find('postingorganisationid').text,

                "api_published": entry.find("published").text,
                "api_updated": entry.find("updated").text,

                "api_category": entry.find("category").get("term"),

                "author_display_name": entry.find("author/name").text,
                "title": entry.find('title').text,
                "content": entry.find('content').text,
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

            self.reviews.append(review)

        # Get the next page url. Be sure to add in the .atom if needed.
        next_page_url = root.find('link[@rel="next"]').get('href')
        if not re.search(r'\.atom', next_page_url):
            next_page_url = re.sub(r'comments', 'comments.atom', next_page_url)
        self.next_page_url = next_page_url

        return None
