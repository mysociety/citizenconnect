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


class ReviewFormTest(TestCase):
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
        self.assertTrue('questions' in resp.context)
        self.assertEqual(resp.context['questions'].count(), 7)
