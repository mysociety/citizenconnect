import datetime
from StringIO import StringIO

import requests
from mock import MagicMock

from selenium.webdriver.common.action_chains import ActionChains

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings
from django.forms.models import model_to_dict

from citizenconnect.browser_testing import SeleniumTestCase
from organisations.tests.models import create_test_organisation
from .models import Review, Question, Answer, Rating
from .forms import ReviewForm
from .management.commands.push_new_reviews_to_choices import Command as PushReviewsCommand


def create_review(organisation, **kwargs):
    attrs = {'email': "bob@example.com",
             'display_name': "Bob Smith",
             'title': "Good review",
             'comment': "Not bad",
             'month_year_of_visit': datetime.date.today()}
    attrs.update(kwargs)
    return organisation.submitted_reviews.create(**attrs)


class ReviewTest(TestCase):

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


class ReviewFormDateCompareTest(TestCase):

    def test_mm_yyyy_date_compare(self):
        tests = [
            # date,      oldest,    result
            ( 3, 2010,   4, 2011,   True ),
            ( 4, 2010,   4, 2011,   True ),
            ( 5, 2010,   4, 2011,   True ),
            ( 3, 2011,   4, 2011,   True ),
            ( 4, 2011,   4, 2011,   False ),
            ( 5, 2011,   4, 2011,   False ),
            ( 3, 2012,   4, 2011,   False ),
            ( 4, 2012,   4, 2011,   False ),
            ( 5, 2012,   4, 2011,   False )
        ]
        
        for mm_a, yyyy_a, mm_b, yyyy_b, expected in tests:
            # print mm_a, yyyy_a, mm_b, yyyy_b, expected
            dt_a = datetime.date(year=yyyy_a, month=mm_a, day=1)
            dt_b = datetime.date(year=yyyy_b, month=mm_b, day=1)
            self.assertEqual(ReviewForm._mm_yyyy_lt_compare_dates(dt_a, dt_b), expected)


class ReviewFormViewBase(object):

    def setUp(self):
        super(ReviewFormViewBase, self).setUp()
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
                                 'agree_to_terms': True,
                                 }

        questions = Question.objects.filter(org_type=self.organisation.organisation_type).order_by('id')

        # store the questions we want to ask
        for prefix, question in enumerate(questions):
            prefix += 1

            answer_index = (prefix-1) % 6
            if answer_index == 5:
                answer_id = ''
            else:
                answer_id = question.answers.all()[answer_index].id

            entry = {}
            entry[str(prefix) + '-question'] = question.id
            entry[str(prefix) + '-answer'] = answer_id
            self.review_post_data.update(entry)

    def assert_review_correctly_stored(self):
        # check details correctly stored
        review = self.organisation.submitted_reviews.all()[0]
        self.assertEqual(model_to_dict(review),  {
            'id': review.id,
            'last_sent_to_api': None,
            'organisation': self.organisation.id,
            'comment': self.review_post_data['comment'],
            'display_name': self.review_post_data['display_name'],
            'email': self.review_post_data['email'],
            'is_anonymous': self.review_post_data['is_anonymous'],
            'month_year_of_visit': datetime.date(self.review_post_data['month_year_of_visit_year'], self.review_post_data['month_year_of_visit_month'], 1),
            'title': self.review_post_data['title']
        })

        # check ratings correctly stored
        for prefix, rating in enumerate(review.ratings.order_by('question__id')):
            prefix = str(prefix + 1)
            # print 'Q: ' + str(rating.question)
            # print 'A: ' + str(rating.answer)

            self.assertEqual(rating.question.id, self.review_post_data[
                             prefix + '-question'])

            answer_id = rating.answer.id if rating.answer else ''
            self.assertEqual(answer_id, self.review_post_data[
                             prefix + '-answer'])

        # check right number in db
        self.assertEqual(
            review.ratings.count(), 6)  # one question not answered


class ReviewFormViewTest(ReviewFormViewBase, TestCase):

    def test_homepage_links_to_reviews(self):
        home_url = reverse('home', kwargs={'cobrand': 'choices'})
        reviews_url = reverse('reviews-pick-provider', kwargs={'cobrand': 'choices'})
        resp = self.client.get(home_url)
        self.assertContains(resp, reviews_url)

    def test_review_form_exists(self):
        resp = self.client.get(self.review_form_url)
        self.assertContains(resp, '<h1>Share Your Experience: %s</h1>' % self.organisation.name, count=1, status_code=200)
        self.assertTrue('organisation' in resp.context)
        self.assertEquals(resp.context['organisation'].pk, self.organisation.pk)
        self.assertTrue('rating_forms' in resp.context)

    def test_submitting_a_valid_review(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 1)

        self.assert_review_correctly_stored()

    def test_submitting_a_review_with_a_future_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        self.review_post_data['month_year_of_visit_year'] = str((datetime.datetime.now() + datetime.timedelta(weeks=53)).year)
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        # For some reason, assertFormError doesn't like this error
        self.assertContains(resp, "The month and year of visit can&#39;t be in the future")

    def test_submitting_a_review_with_a_just_long_enough_ago_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        past_date = datetime.datetime.now() - datetime.timedelta(days=settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS)
        self.review_post_data['month_year_of_visit_year'] = past_date.year
        self.review_post_data['month_year_of_visit_month'] = past_date.month
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assert_review_correctly_stored()

    def test_submitting_a_review_with_a_too_long_ago_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        past_date = datetime.datetime.now() - datetime.timedelta(days=settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS) - datetime.timedelta(days=31)
        self.review_post_data['month_year_of_visit_year'] = past_date.year
        self.review_post_data['month_year_of_visit_month'] = past_date.month
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        # For some reason, assertFormError doesn't like this error
        self.assertContains(resp, "The month and year of visit can&#39;t be more than two years ago")

    def test_form_requires_tandc_agreement(self):
        self.review_post_data['agree_to_terms'] = False
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'agree_to_terms',
                             'You must agree to the terms and conditions to use this service.')

    def test_form_requires_valid_email_address(self):
        self.review_post_data['email'] = 'not an email'
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'email', 'Enter a valid e-mail address.')

    def test_form_requires_visit_date(self):
        self.review_post_data['month_year_of_visit_year'] = None
        self.review_post_data['month_year_of_visit_month'] = None
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'month_year_of_visit', 'Enter a valid date.')

    def test_form_title_and_comment_required(self):
        self.review_post_data['title'] = ''
        self.review_post_data['comment'] = ''
        self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)


class ReviewFormViewBrowserTest(ReviewFormViewBase, SeleniumTestCase):

    def set_rating(self, rating_select_name, score):

        # Find the element
        rating_select = self.driver.find_element_by_name(rating_select_name)

        css_selector = 'div[data-select-name="{0}"] .rateit-range'.format(rating_select_name)
        rating_element = self.driver.find_element_by_css_selector(css_selector)

        # Do the math to work out where on the rating element to click
        element_width = rating_element.size['width']
        element_height = rating_element.size['height']
        star_count = 5
        star_width = element_width / float(star_count)
        horizontal_offset = int(
            score * star_width - star_width / 2)  # can go negative - works for score of 0 :)
        vertical_offset = int(element_height / 2)

        # go to element, position mouse and click.
        ActionChains(self.driver).move_to_element_with_offset(
            rating_element, horizontal_offset, vertical_offset
        ).click(None).perform()

    def get_rating(self, rating_select_name):
        rating_select = self.driver.find_element_by_name(rating_select_name)
        return int(rating_select.get_attribute('value'))

    def test_star_ratings(self):
        d = self.driver
        d.get(self.full_url(self.review_form_url))

        answer_names = []
        for select in d.find_elements_by_css_selector('.review-form__rating-answer select'):
            answer_names.append(select.get_attribute('name'))

        # test setting all possible values and reading that the correct select option is chosen
        for answer_name in answer_names:
            for score in range(6): # 0 for none, and then 1 .. 5
                self.set_rating(answer_name, score)
                self.assertEqual(self.get_rating(answer_name), score)

        # set the values and save, then test correct review is stored
        for answer_name in answer_names:
            desired_answer = self.review_post_data[answer_name]

            if desired_answer:
                desired_rating = Answer.objects.get(pk=desired_answer).star_rating
            else:
                desired_rating = 0

            self.set_rating(answer_name, desired_rating)


        # fill in the text fields
        for name in ['email','display_name','title','comment']:
            d.find_element_by_name(name).send_keys(self.review_post_data[name])

        # tick the boxes
        for name in ['is_anonymous', 'agree_to_terms']:
            checkbox_element = d.find_element_by_name(name)
            # assume they all start out un-checked
            if self.review_post_data[name]:
                checkbox_element.click()

        # select boxes
        for name in ['month_year_of_visit_month', 'month_year_of_visit_year']:
            desired_value = self.review_post_data[name]
            select_element = d.find_element_by_css_selector(
                'select[name="{0}"] option[value="{1}"]'.format(
                    name,
                    desired_value
                )
            ).click()

        # import IPython; IPython.embed()

        # submit form
        d.find_element_by_css_selector('button[type="submit"]').click()


        self.assert_review_correctly_stored()


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

    def test_posts_to_correct_url(self):
        command = PushReviewsCommand()
        self.assertEquals(command.choices_api_url('A111'), "{0}comment/A111?apikey={1}".format(
            settings.NHS_CHOICES_BASE_URL,
            settings.NHS_CHOICES_API_KEY
        ))

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
        self.unsubmitted_review = create_review(self.organisation)
        self.old_review = create_review(self.organisation, last_sent_to_api=(timezone.now() - datetime.timedelta(weeks=2)))
        self.other_old_review = create_review(self.organisation, last_sent_to_api=(timezone.now() - datetime.timedelta(weeks=4)))
        self.newer_review = create_review(self.organisation, last_sent_to_api=(timezone.now() - datetime.timedelta(weeks=1)))

    def test_removes_old_reviews(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 4)
        call_command('remove_reviews_sent_to_choices', stdout=self.stdout, stderr=self.stderr)
        self.assertEquals(self.organisation.submitted_reviews.count(), 2)
