import datetime
from StringIO import StringIO

import requests
from mock import MagicMock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.utils import timezone

from organisations.tests.models import create_test_organisation
from .models import Review, Question, Rating

def create_review(organisation, **kwargs):
    attrs = {'email': "bob@example.com",
            'display_name': "Bob Smith",
            'title': "Good review",
            'comment': "Not bad",
            'month_year_of_visit': datetime.date.today()}
    attrs.update(kwargs)
    return organisation.reviews.create(**attrs)


class ReviewTest(TestCase):
    fixtures = ['questions_and_answers.json']

    def test_creating_a_review(self):
        organisation = create_test_organisation()

        test_question = Question.objects.all()[0]
        test_answer = test_question.answers.all()[0]

        review = Review.objects.create(
            email="bob@example.com",
            display_name="Bob Smith",
            title="Good review",
            comment="Not bad",
            month_year_of_visit=datetime.date.today(),
            organisation=organisation,
        )

        rating = Rating(question=test_question, answer=test_answer)
        review.ratings.add(rating)

        self.assertEqual(review.ratings.count(), 1)


class ReviewFormViewTest(TestCase):
    fixtures = ['questions_and_answers.json']

    def setUp(self):
        self.organisation = create_test_organisation({'ods_code': 'A111'})
        self.review_form_url = reverse('review-form', kwargs={'cobrand': 'choices',
                                                              'ods_code': self.organisation.ods_code})
        self.review_post_data = {'email': 'bob@example.com',
                                 'display_name': 'Bob Smith',
                                 'is_anonymous': False,
                                 'title': 'Good review',
                                 'comment': 'Not bad',
                                 'month_year_of_visit_month': 1,
                                 'month_year_of_visit_year': 2013,
                                 'organisation': self.organisation.id,
                                 '1-question': 1,
                                 '1-answer': 1,
                                 '2-question': 2,
                                 '2-answer': 4,
                                 '3-question': 3,
                                 '3-answer': 10,
                                 '4-question': 4,
                                 '4-answer': 16,
                                 '5-question': 5,
                                 '5-answer': 22,
                                 '6-question': 6,
                                 '6-answer': 26,
                                 '7-question': 7,
                                 '7-answer': 30}

    def test_review_form_exists(self):
        resp = self.client.get(self.review_form_url)
        self.assertContains(resp, 'Reviewing <strong>%s</strong>' % self.organisation.name, count=1, status_code=200)
        self.assertTrue('organisation' in resp.context)
        self.assertEquals(resp.context['organisation'].pk, self.organisation.pk)
        self.assertTrue('rating_forms' in resp.context)

    def test_submitting_a_valid_review(self):
        self.assertEquals(self.organisation.reviews.count(), 0)
        self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.reviews.count(), 1)

    def test_submitting_a_review_with_a_future_date(self):
        self.assertEquals(self.organisation.reviews.count(), 0)
        self.review_post_data['month_year_of_visit_year'] = str((datetime.datetime.now() + datetime.timedelta(weeks=53)).year)
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.reviews.count(), 0)
        # For some reason, assertFormError doesn't like this error
        self.assertContains(resp, "The month and year of visit can&#39;t be in the future")


class PushNewReviewToChoicesCommandTest(TestCase):

    def setUp(self):
        self.organisation = create_test_organisation({'ods_code': 'A111'})
        self.review = create_review(self.organisation)
        self.stdout = StringIO()
        self.stderr = StringIO()

    def mock_api_post_request(self, status, body=''):
        mock_response = MagicMock()
        mock_response.status_code = status
        mock_response.text = body
        requests.post = MagicMock(return_value=mock_response)

    def test_succesful_post_to_api(self):
        self.mock_api_post_request(202)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNotNone(review.last_sent_to_api)
        self.assertEquals("{0}: Sent review to the Choices API\n".format(review.id), self.stdout.getvalue())

    def test_api_returns_invalid_xml_error(self):
        self.mock_api_post_request(400)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The XML has invalid fields\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_api_key_error(self):
        self.mock_api_post_request(401)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The API key does not have permission\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_posting_id_error(self):
        self.mock_api_post_request(403)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: PostingID is a duplicate\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_nacs_code_error(self):
        self.mock_api_post_request(404)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The NACS code A111 is not valid\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_generic_error(self):
        self.mock_api_post_request(500)
        call_command('push_new_reviews_to_choices', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: Server error\n".format(review.id), self.stderr.getvalue())


class RemoveReviewsSentToApiTest(TestCase):
    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.organisation = create_test_organisation()
        self.review = create_review(self.organisation, last_sent_to_api=(timezone.now() - datetime.timedelta(weeks=2)))
        self.other_review = create_review(self.organisation, last_sent_to_api=(timezone.now() - datetime.timedelta(weeks=1)))

    def test_removes_old_reviews(self):
        self.assertEquals(self.organisation.reviews.count(), 2)
        call_command('remove_reviews_sent_to_choices', stdout=self.stdout, stderr=self.stderr)
        self.assertEquals(self.organisation.reviews.count(), 1)
