import datetime
from StringIO import StringIO

import requests
from mock import MagicMock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command

from organisations.tests.models import create_test_organisation
from .models import Review, Question, Answer, Rating


class ReviewTest(TestCase):
    fixtures = ['questions_and_answers.json']

    def test_creating_a_review(self):
        organisation = create_test_organisation()

        test_question = Question.objects.all()[0]
        test_answer = test_question.answer_set.all()[0]

        review = Review.objects.create(
            email="bob@example.com",
            display_name="Bob Smith",
            title="Good review",
            comment="Not bad",
            month_year_of_visit=datetime.date.today(),
            organisation=organisation,
        )

        rating = Rating(question=test_question, answer=test_answer)
        review.rating_set.add(rating)

        self.assertEqual(review.rating_set.count(), 1)


class ReviewFormViewTest(TestCase):
    fixtures = ['questions_and_answers.json']

    def setUp(self):
        self.organisation = create_test_organisation({'ods_code': 'A111'})
        self.review_form_url = reverse('review-form', kwargs={'cobrand': 'choices',
                                                              'ods_code': self.organisation.ods_code})

    def test_review_form_exists(self):
        resp = self.client.get(self.review_form_url)
        self.assertContains(resp, 'Reviewing <strong>%s</strong>' % self.organisation.name, count=1, status_code=200)
        self.assertTrue('organisation' in resp.context)
        self.assertEquals(resp.context['organisation'].pk, self.organisation.pk)
        self.assertTrue('rating_forms' in resp.context)

    def test_submitting_a_valid_review(self):
        self.assertEquals(self.organisation.review_set.count(), 0)
        resp = self.client.post(self.review_form_url, {'email': 'bob@example.com',
                                                       'display_name': 'Bob Smith',
                                                       'is_anonymous': False,
                                                       'title': 'Good review',
                                                       'comment': 'Not bad',
                                                       'month_year_of_visit': '30/05/2013',
                                                       'organisation': self.organisation.id,
                                                       'rating_set-TOTAL_FORMS': 0,
                                                       'rating_set-INITIAL_FORMS': 0,
                                                       'rating_set-MAX_NUM_FORMS': 0,
                                                       'rating_set-0-question': 8,
                                                       'rating_set-1-question': 9,
                                                       'rating_set-1-answer': 36,
                                                       'rating_set-2-question': 10,
                                                       'rating_set-2-answer': 42,
                                                       'rating_set-3-question': 11,
                                                       'rating_set-3-answer': 48,
                                                       'rating_set-4-question': 12,
                                                       'rating_set-5-question': 13,
                                                       'rating_set-0-answer': 55,
                                                       'rating_set-6-question': 14,
                                                       'rating_set-4-answer': 64})

        self.assertEquals(resp.status_code, 302)
        self.assertEquals(self.organisation.review_set.count(), 1)


class PushNewReviewToChoicesCommandTest(TestCase):

    def setUp(self):
        self.organisation = create_test_organisation({'ods_code': 'A111'})
        self.review = self.organisation.review_set.create(
            email="bob@example.com",
            display_name="Bob Smith",
            title="Good review",
            comment="Not bad",
            month_year_of_visit=datetime.date.today(),
        )
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
        self.assertEquals("202: Sent review to the Choices API id={0} ods_code=A111\n".format(review.id), self.stdout.getvalue())

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
