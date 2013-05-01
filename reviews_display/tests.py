import copy

from django.test import TestCase

from organisations.tests.lib import create_test_organisation

from .models import Review, OrganisationFromApiDoesNotExist


class ReviewSaveFromAPITests(TestCase):

    def setUp(self):
        self.organisation = create_test_organisation({"choices_id": 1234})

        self.sample_ratings = [
            {'answer': 'always',
             'question': u'Doctors and nurses worked well together\u2026',
             'score': '5'},
            {'answer': 'Extremely likely',
             'question': 'Friends and Family',
             'score': '5'},
            {'answer': 'clean',
             'question': 'How satisfied are you with the cleanliness of the area you were treated in?',
             'score': '4'},
        ]

        self.sample_review = {
            'api_category': 'comment',
            'api_posting_id': '185684',
            'api_postingorganisationid': '0',
            'api_published': '2013-05-01T12:47:22+01:00',
            'api_updated': '2013-05-01T12:49:12+01:00',
            'author_display_name': 'Fred Smith',
            'title': 'Wonderful staff and treatment',
            'content': 'What a marvelous service the NHS is!',
            'in_reply_to_id': None,
            'organisation_choices_id': str(self.organisation.choices_id),
            'ratings': self.sample_ratings,
        }

    def test_upserts(self):

        # insert entry and check it exists
        self.assertTrue(Review.upsert_from_api_data(self.sample_review))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertEqual(review.title, self.sample_review['title'])

        # do it again (unchanged) and check it is still there
        self.assertTrue(Review.upsert_from_api_data(self.sample_review))

        # upsert with a changed comment and check it is updated
        new_title = "This is the changed title"
        new_sample = self.sample_review.copy()
        new_sample.update({"title": new_title})
        self.assertTrue(Review.upsert_from_api_data(new_sample))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertTrue(review)
        self.assertEqual(review.title, new_title)

    def test_upserts_ratings(self):

        # insert entry and check it exists
        self.assertTrue(Review.upsert_from_api_data(self.sample_review))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )

        # check correctly stored in the db
        ratings = [
            x.as_dict() for x in review.rating_set.all().order_by('question')]
        self.assertEqual(ratings, self.sample_ratings)

        # upsert with changed ratings and check they are updated
        ratings_copy = copy.deepcopy(self.sample_ratings)
        ratings_copy[0]['score'] = 3
        ratings_copy[0]['answer'] = 'so so'
        ratings_copy[3] = {
            'question': 'This is a different question',
            'answer': 'different answer',
            'score': '1',
        }

        new_sample = self.sample_review.copy()
        new_sample['ratings'] = ratings_copy

        self.assertTrue(Review.upsert_from_api_data(new_sample))
        review = Review.objects.get(
            api_posting_id=self.sample_review['api_posting_id']
        )
        self.assertTrue(review)
        self.assertEqual(review.title, new_title)

    def test_takedowns(self):
        self.assertTrue(False)
        # upsert a takedown, check reviews and ratings are deleted

        # upsert a takedown, check reviews and ratings are deleted

    def test_replies(self):
        self.assertTrue(False)
        # upsert a reply, check raises IgnoredCategory exception

    def test_not_found_organisation(self):
        sample_review = self.sample_review.copy()
        sample_review['organisation_choices_id'] = '12345678'  # won't be in db
        self.assertRaises(
            OrganisationFromApiDoesNotExist,
            Review.upsert_from_api_data,
            sample_review
        )
