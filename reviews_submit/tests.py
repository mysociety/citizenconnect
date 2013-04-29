import datetime

from django.test import TestCase

from organisations.tests.models import create_test_organisation
from .models import Review, Question, Answer, Rating


class ReviewTest(TestCase):
    def test_creating_a_review(self):
        organisation = create_test_organisation()

        test_question = Question(title="Everything ok?")
        test_question.save()
        test_answer = Answer(text="Yes", value=1)
        test_question.answer_set.add(test_answer)

        review = Review(
            email="bob@example.com",
            display_name="Bob Smith",
            title="Good review",
            comment="Not bad",
            month_year_of_visit=datetime.date.today(),
            organisation=organisation,
        )

        review.save()
        rating = Rating(question=test_question, answer=test_answer)
        review.rating_set.add(rating)

        self.assertEqual(review.rating_set.count(), 1)

class ReviewFormTest(TestCase):
    def setUp(self):
        self.organisation = create_test_organisation({'ods_code': 'A111'})

    def test_leaving_a_review(self):
        resp = self.client.get('/choices/review/review-form/A111')
        self.assertEqual(resp.status_code, 200)
