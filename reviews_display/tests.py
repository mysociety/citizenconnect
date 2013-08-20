import copy
import os
import json
import datetime
from datetime import timedelta
import urlparse
import mock
import urllib
import pytz
import logging

from django.conf import settings
from django.test import TestCase
from django.forms.models import model_to_dict
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.utils.timezone import utc

from organisations.tests.lib import create_test_organisation, create_test_organisation_parent, AuthorizationTestCase

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


api_posting_id_counter = 185684


def create_test_review(attributes, ratings_attributes=None):
    """Create a test review instance, with optional attributes"""

    # Create a test org to assign the rating to if one's not supplied
    if not attributes.get('organisation'):
        organisation = create_test_organisation({})
    else:
        organisation = attributes.get('organisation')
        del attributes['organisation']

    now = datetime.datetime.utcnow().replace(tzinfo=utc)

    global api_posting_id_counter
    api_posting_id_counter += 1

    default_attributes = {
        'api_category': 'comment',
        'api_posting_id': str(api_posting_id_counter),
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
    instance.organisations.add(organisation)

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
            self.sample_dir,
            'sample.json'
        )

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

    def test_parse_xml_with_no_next_link(self):
        # Issue #1042 - the api code didn't allow for the fact that
        # there might only be one page of reviews coming back, and so
        # the xml wouldn't contain a "next" link at all.
        self.no_next_link_xml_filename = os.path.join(
            self.sample_dir,
            'sample_no_next_link.xml'
        )

        self.no_next_link_xml = open(self.no_next_link_xml_filename).read()

        api = ReviewsAPI(organisation_type="hospitals")
        xml = api.cleanup_xml(self.no_next_link_xml)

        # This threw an error before
        next_page_url = api.extract_next_page_url(xml)

        self.assertIsNone(next_page_url)


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
            'in_reply_to_organisation_id': None,
            'organisation_choices_id': str(self.organisation.choices_id),
            'ratings': self.sample_ratings,
        }

    def test_main_rating_score_returns_friends_and_family_rating_score_if_present(self):
        rating_attributes = {'answer': 'Extremely likely',
                             'question': 'Friends and Family',
                             'score': 5}
        review = create_test_review({'organisation': self.organisation}, [rating_attributes])
        self.assertEqual(review.main_rating_score, 5)

    def test_main_rating_score_returns_none_if_friends_and_family_rating_not_present(self):
        rating_attributes = {'answer': 'Yes',
                             'question': 'Clean',
                             'score': 5}
        review = create_test_review({'organisation': self.organisation}, [rating_attributes])
        self.assertEqual(review.main_rating_score, None)

    def test_upsert_or_deletes(self):

        # insert entry and check it exists
        self.assertTrue(Review.upsert_or_delete_from_api_data(self.sample_review, self.organisation.organisation_type))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertEqual(review.title, self.sample_review['title'])
        self.assertEqual(review.content, self.sample_review['content'])
        self.assertEqual(review.content_liked, self.sample_review['content_liked'])
        self.assertEqual(review.content_improved, self.sample_review['content_improved'])

        # do it again (unchanged) and check it is still there
        self.assertTrue(Review.upsert_or_delete_from_api_data(self.sample_review, self.organisation.organisation_type))

        # upsert_or_delete with a changed comment and check it is updated
        new_title = "This is the changed title"
        new_sample = self.sample_review.copy()
        new_sample.update({"title": new_title})
        self.assertTrue(Review.upsert_or_delete_from_api_data(new_sample, self.organisation.organisation_type))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertTrue(review)
        self.assertEqual(review.title, new_title)

        # upsert_or_delete with published as too old and check it is deleted
        outdated_sample = self.sample_review.copy()
        outdated_sample.update({"api_published": '2010-05-01T12:47:22+01:00'})
        Review.upsert_or_delete_from_api_data(outdated_sample, self.organisation.organisation_type)
        self.assertEqual(
            Review.objects.filter(
                api_posting_id=self.sample_review['api_posting_id']
            ).count(),
            0
        )

        # check running again on entry that is not there
        Review.upsert_or_delete_from_api_data(outdated_sample, self.organisation.organisation_type)

    def test_upsert_or_deletes_ratings(self):
        self.maxDiff = None

        # insert entry and check it exists
        self.assertTrue(Review.upsert_or_delete_from_api_data(self.sample_review, self.organisation.organisation_type))
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

        self.assertTrue(Review.upsert_or_delete_from_api_data(new_sample, self.organisation.organisation_type))
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

    def test_upserts_or_deletes_gp_review(self):
        # Create a test gp surgery
        gp_surgery = create_test_organisation_parent({'code': 'GP1', 'choices_id': 5678})
        # Give it two branches
        gp_branch1 = create_test_organisation({'ods_code': 'GP1B1', 'parent': gp_surgery})
        gp_branch2 = create_test_organisation({'ods_code': 'GP1B2', 'parent': gp_surgery})
        self.assertEqual(gp_surgery.organisations.all().count(), 2)

        sample_gp_review = self.sample_review.copy()
        sample_gp_review['organisation_choices_id'] = gp_surgery.choices_id

        # insert entry and check it exists on both branches
        self.assertTrue(Review.upsert_or_delete_from_api_data(sample_gp_review, 'gppractices'))
        review = Review.objects.get(
            api_posting_id=sample_gp_review['api_posting_id']
        )
        self.assertEqual(review.title, sample_gp_review['title'])
        self.assertEqual(review.content, sample_gp_review['content'])
        self.assertEqual(review.content_liked, sample_gp_review['content_liked'])
        self.assertEqual(review.content_improved, sample_gp_review['content_improved'])
        self.assertEqual(list(review.organisations.all()), [gp_branch1, gp_branch2])

        # do it again (unchanged) and check it is still there
        self.assertTrue(Review.upsert_or_delete_from_api_data(sample_gp_review, 'gppractices'))

        # upsert_or_delete with a changed comment and check it is updated
        new_title = "This is the changed title"
        new_sample = sample_gp_review.copy()
        new_sample.update({"title": new_title})
        self.assertTrue(Review.upsert_or_delete_from_api_data(new_sample, 'gppractices'))
        review = Review.objects.get(
            api_posting_id=sample_gp_review['api_posting_id']
        )
        self.assertTrue(review)
        self.assertEqual(review.title, new_title)
        self.assertEqual(list(review.organisations.all()), [gp_branch1, gp_branch2])

        # upsert_or_delete with published as too old and check it is deleted
        outdated_sample = sample_gp_review.copy()
        outdated_sample.update({"api_published": '2010-05-01T12:47:22+01:00'})
        Review.upsert_or_delete_from_api_data(outdated_sample, 'gppractices')
        self.assertEqual(
            Review.objects.filter(
                api_posting_id=self.sample_review['api_posting_id']
            ).count(),
            0
        )

        # check running again on entry that is not there
        Review.upsert_or_delete_from_api_data(outdated_sample, 'gppractices')

    def test_takedowns(self):
        # insert entry
        Review.upsert_or_delete_from_api_data(self.sample_review, self.organisation.organisation_type)

        # upsert_or_delete a takedown, check review is deleted
        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'deletion'
        Review.upsert_or_delete_from_api_data(sample_review, self.organisation.organisation_type)
        self.assertEqual(
            Review.objects.filter(
                api_posting_id=sample_review['api_posting_id']
            ).count(),
            0
        )

        # check that calling it without anything is db is ok too
        Review.upsert_or_delete_from_api_data(sample_review, self.organisation.organisation_type)

    def test_reply(self):
        review = create_test_review({'organisation': self.organisation}, {})

        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'reply'
        sample_review['in_reply_to_id'] = review.api_posting_id
        sample_review['in_reply_to_organisation_id'] = review.api_postingorganisationid

        Review.upsert_or_delete_from_api_data(sample_review, self.organisation.organisation_type)

        reply = Review.objects.get(api_posting_id=sample_review['api_posting_id'])

        self.assertEqual(reply.in_reply_to, review)
        self.assertEqual(list(review.replies.all()), [reply])

    def test_reply_where_original_does_not_exist(self):
        sample_review = self.sample_review.copy()
        sample_review['api_category'] = 'reply'
        sample_review['in_reply_to_id'] = '1234567'  # does not exist
        sample_review['in_reply_to_organisation_id'] = '0'

        self.assertRaises(
            RepliedToReviewDoesNotExist,
            Review.upsert_or_delete_from_api_data,
            sample_review,
            'hospitals'
        )

    def test_not_found_organisation(self):
        sample_review = self.sample_review.copy()
        sample_review['organisation_choices_id'] = '12345678'  # won't be in db
        self.assertRaises(
            OrganisationFromApiDoesNotExist,
            Review.upsert_or_delete_from_api_data,
            sample_review,
            'hospitals'
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

    def test_summary_property(self):
        # Test summary returns "See more..." when content is empty
        # and truncates to 20 words if not
        review = create_test_review({'organisation': self.organisation}, {})
        review.content = "Something that is awfully long, much longer in fact than the twenty words or so that we have set the summary field to truncate to"
        review.save()

        self.assertEqual(review.summary, "Something that is awfully long, much longer in fact than the twenty words or so that we have set the...")

        review.content = ''
        review.save()

        self.assertEqual(review.summary, "See more...")


class OrganisationReviewsTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': 'ABC'})
        self.test_other_organisation = create_test_organisation(
            {'ods_code': 'DEF'}
        )
        self.org_review = create_test_review(
            {'organisation': self.test_organisation},
            {}
        )
        self.other_org_review = create_test_review(
            {'organisation': self.test_other_organisation},
            {}
        )
        self.reviews_list_url = reverse(
            'organisation-reviews',
            kwargs={
                'ods_code': self.test_organisation.ods_code,
                'cobrand': 'choices'
            }
        )

    def test_organisation_reviews_page(self):
        resp = self.client.get(self.reviews_list_url)
        self.assertEqual(resp.context['organisation'], self.test_organisation)
        self.assertEqual(len(resp.context['table'].rows), 1)
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)

    def test_organisation_reviews_page_links_to_review(self):
        # Issue #1083 - the row_href on the table class used by this view
        # didn't exist, but the display code expected it to in order to populate
        # data-href
        expected_review_url = reverse(
            'review-detail',
            kwargs={
                'cobrand': 'choices',
                'ods_code': self.test_organisation.ods_code,
                'api_posting_id': self.org_review.api_posting_id
            }
        )
        resp = self.client.get(self.reviews_list_url)
        self.assertContains(resp, 'data-href="{0}"'.format(expected_review_url))
        self.assertContains(resp, '<a href="{0}">'.format(expected_review_url))

    def test_organisation_reviews_page_links_to_correct_cobrand(self):
        mhl_reviews_list_url = reverse(
            'organisation-reviews',
            kwargs={
                'ods_code': self.test_organisation.ods_code,
                'cobrand': 'myhealthlondon'
            }
        )
        # The choices cobrand was hardcoded
        expected_review_url = reverse(
            'review-detail',
            kwargs={
                'cobrand': 'myhealthlondon',
                'ods_code': self.test_organisation.ods_code,
                'api_posting_id': self.org_review.api_posting_id
            }
        )
        resp = self.client.get(mhl_reviews_list_url)
        self.assertContains(resp, 'data-href="{0}"'.format(expected_review_url))
        self.assertContains(resp, '<a href="{0}">'.format(expected_review_url))

    def test_replies_not_shown_in_list(self):
        # Issues #1089 - Replies were showing up in the
        # list as well as reviews

        # Add a reply to one of the reviews
        org_review_reply = create_test_review(
            {'organisation': self.test_organisation},
            {}
        )
        org_review_reply.in_reply_to = self.org_review
        org_review_reply.save()
        resp = self.client.get(self.reviews_list_url)
        # There should still only be one review in the table
        self.assertEqual(len(resp.context['table'].rows), 1)
        # It should be the review, not the reply
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)

    def test_reviews_shown_in_descending_published_order(self):
        # Add a new review from the past
        old_date = datetime.datetime.utcnow().replace(tzinfo=utc) - timedelta(days=10)
        # Create this one first to double-check it's not in any other ordering
        older_review = create_test_review(
            {
                'organisation': self.test_organisation,
                'api_published': old_date - timedelta(days=10)
            },
            {}
        )
        old_review = create_test_review(
            {
                'organisation': self.test_organisation,
                'api_published': old_date
            },
            {}
        )
        resp = self.client.get(self.reviews_list_url)
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)
        self.assertEqual(resp.context['table'].rows[1].record, old_review)
        self.assertEqual(resp.context['table'].rows[2].record, older_review)

    def test_summary_shown_for_review(self):
        resp = self.client.get(self.reviews_list_url)
        self.assertContains(resp, self.org_review.summary)

        self.org_review.content = ""
        self.org_review.save()
        resp = self.client.get(self.reviews_list_url)
        self.assertContains(resp, self.org_review.summary)


class OrganisationParentReviewsTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationParentReviewsTests, self).setUp()
        self.org_review = create_test_review({
            'organisation': self.test_hospital},
            {}
        )
        self.other_org_review = create_test_review({'organisation': self.test_gp_branch}, {})
        self.reviews_list_url = reverse(
            'org-parent-reviews',
            kwargs={
                'code': self.test_trust.code,
            }
        )

    def test_trust_reviews_page(self):
        expected_review_url = reverse(
            'review-detail',
            kwargs={
                'cobrand': 'choices',
                'ods_code': self.test_hospital.ods_code,
                'api_posting_id': self.org_review.api_posting_id
            }
        )
        self.login_as(self.trust_user)
        resp = self.client.get(self.reviews_list_url)
        self.assertEqual(resp.context['organisation_parent'], self.test_trust)
        self.assertEqual(len(resp.context['table'].rows), 1)
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)
        self.assertContains(resp, 'data-href="{0}"'.format(expected_review_url))
        self.assertContains(resp, '<a href="{0}">'.format(expected_review_url))

    def test_replies_not_shown_in_list(self):
        # Issues #1089 - Replies were showing up in the
        # list as well as reviews

        # Add a reply to one of the reviews
        org_review_reply = create_test_review(
            {'organisation': self.test_hospital},
            {}
        )
        org_review_reply.in_reply_to = self.org_review
        org_review_reply.save()
        self.login_as(self.trust_user)
        resp = self.client.get(self.reviews_list_url)
        # There should still only be one review in the table
        self.assertEqual(len(resp.context['table'].rows), 1)
        # It should be the review, not the reply
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)

    def test_reviews_shown_in_descending_published_order(self):
        # Add a new review from the past
        old_date = datetime.datetime.utcnow().replace(tzinfo=utc) - timedelta(days=10)
        # Create this one first to double check it's not in any other ordering
        older_review = create_test_review(
            {
                'organisation': self.test_hospital,
                'api_published': old_date - timedelta(days=10)
            },
            {}
        )
        old_review = create_test_review(
            {
                'organisation': self.test_hospital,
                'api_published': old_date
            },
            {}
        )
        self.login_as(self.trust_user)
        resp = self.client.get(self.reviews_list_url)
        self.assertEqual(resp.context['table'].rows[0].record, self.org_review)
        self.assertEqual(resp.context['table'].rows[1].record, old_review)
        self.assertEqual(resp.context['table'].rows[2].record, older_review)

    def test_can_sort_by_provider_name(self):
        # Issues #1118 - Sorting by provider name had an issue with the Accessor
        # used, for some reason Django-Tables2 introspects differently when
        # ordering than when just displaying, so what worked for one didn't for
        # this other. The solution was to specify a different Accessor for
        # the ordering: http://django-tables2.readthedocs.org/en/latest/#specifying-alternative-ordering-for-a-column
        ordered_reviews_list_url = "{0}?sort=-organisation_name".format(self.reviews_list_url)
        self.login_as(self.trust_user)
        # This would 500 before we fixed it
        resp = self.client.get(ordered_reviews_list_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_shown_for_review(self):
        self.login_as(self.trust_user)
        resp = self.client.get(self.reviews_list_url)
        self.assertContains(resp, self.org_review.summary)

        self.org_review.content = ""
        self.org_review.save()
        self.login_as(self.trust_user)
        resp = self.client.get(self.reviews_list_url)
        self.assertContains(resp, self.org_review.summary)


class ReviewDetailTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': 'ABC'})
        self.org_review = create_test_review({
                                             'organisation': self.test_organisation}, {})
        self.org_reply = create_test_review({
                                             'organisation': self.test_organisation,
                                             'in_reply_to_id': self.org_review.id,
                                             'api_category': 'reply',
                                             }, {})

    def test_organisation_reviews_page(self):
        review_detail_url = reverse('review-detail',
                                    kwargs={
                                        'ods_code': self.test_organisation.ods_code,
                                    'api_posting_id': self.org_review.api_posting_id,
                                    'cobrand': 'choices'})
        resp = self.client.get(review_detail_url)
        self.assertEqual(resp.context['organisation'], self.test_organisation)
        self.assertEqual(resp.context['object'], self.org_review)

    def test_organisation_reviews_page_404s_for_reply(self):
        review_detail_url = reverse('review-detail',
                                    kwargs={
                                        'ods_code': self.test_organisation.ods_code,
                                    'api_posting_id': self.org_reply.api_posting_id,
                                    'cobrand': 'choices'})

        # disable logging of "Not Found"
        logger = logging.getLogger('django.request')
        previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        resp = self.client.get(review_detail_url)

        # restore logger
        logger.setLevel(previous_level)

        self.assertEqual(resp.status_code, 404)
