import copy
import os
import json
import datetime
import urlparse
import mock
import urllib
import pytz

from django.conf import settings
from django.test import TestCase
from django.forms.models import model_to_dict
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.timezone import utc

from organisations.tests.lib import create_test_organisation

from .models import Review, OrganisationFromApiDoesNotExist, RepliedToReviewDoesNotExist
from .reviews_api import ReviewsAPI


def create_test_rating(attributes, review):
    """Create a test rating instance for a review, with optional attributes"""

    default_attributes = {
        'answer': 'Extremely likely',
        'question': 'Friends and Family',
        'score': 5,
        'review': review
    }
    default_attributes.update(attributes)
    instance = review.ratings.create(**dict((k, v) for (
        k, v) in default_attributes.items() if '__' not in k))
    review.save()
    return instance


def create_test_review(attributes, ratings_attributes):
    """Create a test review instance, with optional attributes"""

    # Create a test org to assign the rating to if one's not supplied
    if not attributes.get('organisation'):
        organisation = create_test_organisation({})
        attributes['organisation'] = organisation

    now = datetime.datetime.utcnow().replace(tzinfo=utc)
    default_attributes = {
        'api_category': 'comment',
        'api_posting_id': '185684',
        'api_postingorganisationid': '0',
        'api_published': now,
        'api_updated': now,
        'author_display_name': 'Fred Smith',
        'title': 'Wonderful staff and treatment',
        'content_liked': 'Things I liked',
        'content_improved': 'Things that could be improved',
        'content': 'What a marvellous service the NHS is!',
    }

    default_attributes.update(attributes)
    instance = Review(**dict((k, v) for (
        k, v) in default_attributes.items() if '__' not in k))
    instance.save()

    # Create some dummy ratings if there are none supplied
    if not ratings_attributes:
        ratings_attributes = [
            {'answer': 'always',
             'question': u'Doctors and nurses worked well together\u2026',
             'score': 5},
            {'answer': 'Extremely likely',
             'question': 'Friends and Family',
             'score': 5},
            {'answer': 'clean',
             'question': 'How satisfied are you with the cleanliness of the area you were treated in?',
             'score': 4},
        ]
    for rating_attributes in ratings_attributes:
        create_test_rating(rating_attributes, instance)

    return instance


class ReviewNextPageURLTests(TestCase):

    def test_next_page_url_correctly_set_at_init(self):

        tests = {
            '/foo/bar': dict(
                organisation_type='hospitals',
                start_page='http://example.org/foo/bar?baz'),
            '/organisations/hospitals/comments.atom': dict(
                organisation_type="hospitals"),
            '/organisations/gppractices/comments.atom': dict(
                organisation_type="gppractices"),
            '/organisations/hospitals/commentssince/2012/10/5.atom': dict(
                organisation_type='hospitals',
                since=datetime.date(2012, 10, 5)),
        }

        for expected, kwargs in tests.items():
            api = ReviewsAPI(**kwargs)
            path = urlparse.urlparse(api.next_page_url).path
            self.assertEqual(path, expected)


class SampleDirMixin(object):

    def setUp(self):
        self.sample_dir = os.path.join(
            os.path.dirname(__file__),
            'test_sample_data'
        )


class ReviewParseApiXmlTests(SampleDirMixin, TestCase):

    def setUp(self):
        super(ReviewParseApiXmlTests, self).setUp()
        self.sample_xml_filename = os.path.join(self.sample_dir, 'sample.xml')
        self.sample_json_filename = os.path.join(
            self.sample_dir, 'sample.json')

        self.xml = open(self.sample_xml_filename).read()
        self.json = json.loads(open(self.sample_json_filename).read())

    def test_parse_sample_xml(self):
        expected = self.json

        api = ReviewsAPI(organisation_type="hospitals")
        xml = api.cleanup_xml(self.xml)
        actual = api.extract_reviews_from_xml(xml)

        # Handy for recreating the JSON when testing
        # open(
        #     self.sample_json_filename, 'w'
        # ).write(
        #     json.dumps(
        #         actual, sort_keys=True, indent=4, separators=(',', ': ')
        #     )
        # )

        self.maxDiff = None
        self.assertEqual(actual, expected)


class ReviewParseEmptyApiXmlTests(SampleDirMixin, TestCase):

    def test_mocked_up_empty_response(self):

        # If there are no entries fond the response is a 404 with HTML which
        # means we need to special case it in the code. If it were a 200 with
        # atom and no entries the special casing would not be needed an a test
        # like that in ReviewParseApiXmlTests would suffice (with a different
        # sample xml file).

        # create the mock response
        mock_response = mock.Mock()
        mock_response.getcode = mock.MagicMock(return_value=404)
        mock_response.read = mock.MagicMock(
            return_value=open(os.path.join(self.sample_dir, '404.html')).read()
        )

        # mock urllib's urlopen
        with mock.patch.object(urllib, 'urlopen', return_value=mock_response):
            api = ReviewsAPI(organisation_type="hospitals")

            for review in api:
                self.assertTrue(False, 'should never reach here')

            self.assertTrue(True, "did not go into loop")
            self.assertEqual(api.next_page_url, None)

        # test that these two methods correctly cope with xml that is None
        self.assertEqual(api.extract_reviews_from_xml(None), [])
        self.assertEqual(api.extract_next_page_url(None), None)


class ReviewModelTests(TestCase):

    def setUp(self):
        self.organisation = create_test_organisation({"choices_id": 1234})

        self.sample_ratings = [
            {'answer': 'always',
             'question': u'Doctors and nurses worked well together\u2026',
             'score': 5},
            {'answer': 'Extremely likely',
             'question': 'Friends and Family',
             'score': 5},
            {'answer': 'clean',
             'question': 'How satisfied are you with the cleanliness of the area you were treated in?',
             'score': 4},
        ]

        self.sample_review = {
            'api_category': 'comment',
            'api_posting_id': '185684',
            'api_postingorganisationid': '0',
            'api_published': '2013-05-01T12:47:22+01:00',
            'api_updated': '2013-05-01T12:49:12+01:00',
            'author_display_name': 'Fred Smith',
            'title': 'Wonderful staff and treatment',
            'content_liked': 'Things I liked',
            'content_improved': 'Things that could be improved',
            'content': 'What a marvellous service the NHS is!',
            'in_reply_to_id': None,
            'organisation_choices_id': str(self.organisation.choices_id),
            'ratings': self.sample_ratings,
        }

    def test_upsert_or_deletes(self):

        # insert entry and check it exists
        self.assertTrue(Review.upsert_or_delete_from_api_data(
            self.sample_review))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertEqual(review.title, self.sample_review['title'])
        self.assertEqual(review.content, self.sample_review['content'])
        self.assertEqual(review.content_liked, self.sample_review['content_liked'])
        self.assertEqual(review.content_improved, self.sample_review['content_improved'])

        # do it again (unchanged) and check it is still there
        self.assertTrue(Review.upsert_or_delete_from_api_data(
            self.sample_review))

        # upsert_or_delete with a changed comment and check it is updated
        new_title = "This is the changed title"
        new_sample = self.sample_review.copy()
        new_sample.update({"title": new_title})
        self.assertTrue(Review.upsert_or_delete_from_api_data(new_sample))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertTrue(review)
        self.assertEqual(review.title, new_title)

        # upsert_or_delete with published as too old and check it is deleted
        outdated_sample = self.sample_review.copy()
        outdated_sample.update({"api_published": '2010-05-01T12:47:22+01:00'})
        Review.upsert_or_delete_from_api_data(outdated_sample)
        self.assertEqual(
            Review.objects.filter(
                api_posting_id=self.sample_review['api_posting_id']
            ).count(),
            0
        )

        # check running again on entry that is not there
        Review.upsert_or_delete_from_api_data(outdated_sample)

    def test_upsert_or_deletes_ratings(self):
        self.maxDiff = None

        # insert entry and check it exists
        self.assertTrue(Review.upsert_or_delete_from_api_data(
            self.sample_review))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )

        # check correctly stored in the db
        ratings = [
            model_to_dict(x, exclude=['id', 'review'])
            for x
            in review.ratings.all().order_by('question')
        ]
        self.assertEqual(ratings, self.sample_ratings)

        # upsert_or_delete with changed ratings and check they are updated
        ratings_copy = copy.deepcopy(self.sample_ratings)
        ratings_copy[0]['score'] = 3
        ratings_copy[0]['answer'] = 'so so'
        ratings_copy[2] = {
            'question': 'This is a different question',
            'answer': 'different answer',
            'score': 1,
        }

        new_sample = self.sample_review.copy()
        new_sample['ratings'] = ratings_copy

        self.assertTrue(Review.upsert_or_delete_from_api_data(new_sample))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )

        # check correctly stored in the db
        ratings = [
            model_to_dict(x, exclude=['id', 'review'])
            for x
            in review.ratings.all().order_by('question')
        ]
        self.assertEqual(ratings, ratings_copy)

    def test_takedowns(self):
        # insert entry
        Review.upsert_or_delete_from_api_data(self.sample_review)

        # upsert_or_delete a takedown, check review is deleted
        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'deletion'
        Review.upsert_or_delete_from_api_data(sample_review)
        self.assertEqual(
            Review.objects.filter(
                api_posting_id=sample_review['api_posting_id']
            ).count(),
            0
        )

        # check that calling it without anything is db is ok too
        Review.upsert_or_delete_from_api_data(sample_review)

    def test_reply(self):
        review = create_test_review({'organisation': self.organisation}, {})

        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'reply'
        sample_review['in_reply_to_id'] = review.api_posting_id

        Review.upsert_or_delete_from_api_data(sample_review)

        reply = Review.objects.get(api_posting_id=sample_review['api_posting_id'])

        self.assertEqual(reply.in_reply_to, review)
        self.assertEqual(list(review.replies.all()), [reply])


    def test_reply_where_original_does_not_exist(self):
        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'reply'
        sample_review['in_reply_to_id'] = '1234567' # does not exist

        self.assertRaises(
            RepliedToReviewDoesNotExist,
            Review.upsert_or_delete_from_api_data,
            sample_review
        )


    def test_not_found_organisation(self):
        sample_review = self.sample_review.copy()
        sample_review['organisation_choices_id'] = '12345678'  # won't be in db
        self.assertRaises(
            OrganisationFromApiDoesNotExist,
            Review.upsert_or_delete_from_api_data,
            sample_review
        )

    def test_delete_old_reviews(self):

        # put a couple of test reviews in the db
        test_age_in_days = settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS + 10
        old_review = create_test_review({
            'organisation': self.organisation,
            'api_published': datetime.datetime.now(pytz.utc) - datetime.timedelta(days=test_age_in_days)
        }, {})
        young_review = create_test_review({
            'organisation': self.organisation,
        }, {})

        # run the delete_old_reviews management command
        call_command('delete_old_reviews')

        # Check that the young one remains, old one is gone
        self.assertFalse(Review.objects.filter(pk=old_review.id).exists())
        self.assertTrue(Review.objects.filter(pk=young_review.id).exists())


class ReviewOrganisationListTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': 'ABC'})
        self.test_other_organisation = create_test_organisation(
            {'ods_code': 'DEF'})
        self.org_review = create_test_review({
                                             'organisation': self.test_organisation}, {})
        self.other_org_review = create_test_review({
                                                   'organisation': self.test_other_organisation}, {})

    def test_organisation_reviews_page(self):
        reviews_list_url = reverse('review-organisation-list',
                                   kwargs={
                                       'ods_code': self.test_organisation.ods_code,
                                   'cobrand': 'choices'})
        resp = self.client.get(reviews_list_url)
        self.assertEqual(resp.context['organisation'], self.test_organisation)
        self.assertEqual(len(resp.context['table'].rows), 1)
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)


class ReviewDetailTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': 'ABC'})
        self.org_review = create_test_review({
                                             'organisation': self.test_organisation}, {})

    def test_organisation_reviews_page(self):
        review_detail_url = reverse('review-detail',
                                    kwargs={
                                        'ods_code': self.test_organisation.ods_code,
                                    'pk': self.org_review.id,
                                    'cobrand': 'choices'})
        resp = self.client.get(review_detail_url)
        self.assertEqual(resp.context['organisation'], self.test_organisation)
        self.assertEqual(resp.context['object'], self.org_review)
