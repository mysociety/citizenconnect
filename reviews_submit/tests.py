import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse

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
