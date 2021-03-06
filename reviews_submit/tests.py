import datetime
import logging
from StringIO import StringIO

import requests
from mock import MagicMock
from dateutil import relativedelta

from selenium.webdriver.common.action_chains import ActionChains

from django.test import TestCase
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.utils import timezone
from django.conf import settings
from django.forms.models import model_to_dict

from citizenconnect.browser_testing import SeleniumTestCase
from organisations.tests.models import create_test_organisation, create_test_organisation_parent
from .models import Review, Question, Answer, Rating
from .forms import ReviewForm
from .management.commands.send_new_reviews_to_choices_api import Command as PushReviewsCommand


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

    def test_handles_unicode(self):
        # Issue #1189 led me to check the rest of the codebase, and this class
        # exhibited the same bug - potential unicode being inserted into an
        # ascii string using format()
        organisation = create_test_organisation()

        test_question = Question.objects.all()[0]
        test_answer = test_question.answers.all()[0]

        review = Review.objects.create(
            email="bob@example.com",
            display_name=u"Bob Smith \u2019",
            title=u"Good review \u2019",
            comment=u"Not bad \u2019",
            month_year_of_visit=datetime.date.today(),
            organisation=organisation,
        )

        rating = Rating(question=test_question, answer=test_answer)
        review.ratings.add(rating)

        self.assertEqual(review.__unicode__(), u"Bob Smith \u2019 - Good review \u2019")


class RatingTest(TestCase):

    def test_unicode_doesnt_break_when_no_answer(self):
        # Issue #1259 - the __unicode__() method tried to print a string
        # containing the answer title, but answer is a nullable field
        test_question = Question.objects.all()[0]
        rating = Rating(question=test_question)

        self.assertEqual(rating.__unicode__(), u"{0}".format(test_question.title))

        # Test with an answer too
        test_answer = test_question.answers.all()[0]
        rating.answer = test_answer

        self.assertEqual(rating.__unicode__(), u"{0} - {1}".format(test_question.title, test_answer.text))


class ReviewFormMonthChoicesTest(TestCase):

    def test_month_choices(self):
        this_year = datetime.date.today().year
        this_month = datetime.date.today().month
        first_of_month = datetime.date(this_year, this_month, 1)
        twenty_four_months_ago = first_of_month - relativedelta.relativedelta(years=2)

        choices = [x for x in ReviewForm._month_choices()]

        self.assertEqual(choices[-1], (first_of_month.strftime("%Y-%m-%d"), first_of_month.strftime("%B %Y")))
        self.assertEqual(choices[0], (twenty_four_months_ago.strftime("%Y-%m-%d"), twenty_four_months_ago.strftime("%B %Y")))
        self.assertEqual(len(choices), 25)


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
                                 'month_year_of_visit': datetime.date(2013, 1, 1),
                                 'organisation': self.organisation.id,
                                 'agree_to_terms': True,
                                 'website': '',  # honeypot - should be blank
                                 }

        questions = Question.objects.filter(org_type=self.organisation.organisation_type).order_by('id')
        self.questions = questions

        # store the questions we want to ask
        for counter, question in enumerate(questions):
            prefix = str(question.id)

            answer_index = counter % 6
            if answer_index == 5:
                answer_id = ''
            else:
                answer_id = question.answers.all()[answer_index].id

            # Set all required questions to have an answer
            if question.is_required:
                answer_id = question.answers.all()[0].id

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
            'month_year_of_visit': self.review_post_data['month_year_of_visit'],
            'title': self.review_post_data['title']
        })

        # check ratings correctly stored
        for rating in review.ratings.all():
            prefix = str(rating.question.id)
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
        self.assertTrue('required_rating_forms' in resp.context)
        self.assertTrue('optional_rating_forms' in resp.context)

    def test_submitting_a_valid_review(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 1)

        self.assert_review_correctly_stored()

    def test_submitting_a_review_with_a_future_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        future_date = datetime.date.today() + datetime.timedelta(weeks=53)
        self.review_post_data['month_year_of_visit'] = future_date
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        expected_error = 'Select a valid choice. {0} is not one of the available choices.'.format(future_date.strftime("%Y-%m-%d"))
        self.assertFormError(resp, 'form', 'month_year_of_visit', expected_error)

    def test_submitting_a_review_with_a_just_long_enough_ago_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        past_date = datetime.date(datetime.date.today().year, datetime.date.today().month, 1) - relativedelta.relativedelta(years=2)
        self.review_post_data['month_year_of_visit'] = past_date
        self.client.post(self.review_form_url, self.review_post_data)
        self.assert_review_correctly_stored()

    def test_submitting_a_review_with_a_too_long_ago_date(self):
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        past_date = datetime.date.today() - datetime.timedelta(days=settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS) - datetime.timedelta(days=31)
        self.review_post_data['month_year_of_visit'] = past_date
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)
        expected_error = 'Select a valid choice. {0} is not one of the available choices.'.format(past_date.strftime("%Y-%m-%d"))
        self.assertFormError(resp, 'form', 'month_year_of_visit', expected_error)

    def test_form_requires_tandc_agreement(self):
        self.review_post_data['agree_to_terms'] = False
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'agree_to_terms', 'You must agree to the terms and conditions to use this service.')

    def test_form_requires_valid_email_address(self):
        self.review_post_data['email'] = 'not an email'
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'email', 'Enter a valid e-mail address.')

    def test_form_requires_visit_date(self):
        del self.review_post_data['month_year_of_visit']
        resp = self.client.post(self.review_form_url, self.review_post_data)
        self.assertFormError(resp, 'form', 'month_year_of_visit', 'This field is required.')

    def test_form_title_and_comment_required(self):
        self.review_post_data['title'] = ''
        self.review_post_data['comment'] = ''
        self.client.post(self.review_form_url, self.review_post_data)
        self.assertEquals(self.organisation.submitted_reviews.count(), 0)

    def test_leaving_required_rating_empty(self):
        required_questions = self.questions.filter(is_required=True)
        self.assertTrue(len(required_questions), "Need some required questions for this test")

        prefix = str(required_questions[0].id)
        del self.review_post_data[prefix + '-answer']

        resp = self.client.post(self.review_form_url, self.review_post_data)

        # Would be better to use assertFormSetError from
        #  https://code.djangoproject.com/ticket/11603 here, but it's a
        # Django 1.6 thing
        self.assertContains(
            resp,
            'Rating is required.'
        )

        # check that we've not been redirected
        self.assertEqual(resp.status_code, 200) # not a redirect

    def test_form_fails_if_website_given(self):

        # get the form, check the website field is shown
        resp = self.client.get(self.review_form_url)
        self.assertContains(resp, '<input type="text" name="website"')

        # post spammy data, check it is not accepted
        spam_review = self.review_post_data.copy()
        spam_review['website'] = 'http://cheap-drugs.com/'
        resp = self.client.post(self.review_form_url, spam_review)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('has been rejected' in resp.content)
        self.assertEqual(self.organisation.submitted_reviews.count(), 0)

    def test_form_404s_if_org_not_found(self):
        # Issue #1245 - review form view didn't use get_object_or_404
        # so we got errors when someone tried to hack the url instead of them
        # just getting a 404

        # Silence the output, because the 404 will be printed otherwise
        logging.disable(logging.CRITICAL)
        bad_org_form_url = reverse('review-form', kwargs={'cobrand': 'choices',
                                                          'ods_code': 'BAD'})
        resp = self.client.get(bad_org_form_url)
        self.assertEqual(resp.status_code, 404)

        # Reset our logging to normal
        logging.disable(logging.NOTSET)


class ReviewFormViewBrowserTest(ReviewFormViewBase, SeleniumTestCase):

    def set_rating(self, rating_select_name, score):

        # Find the element
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
        d.find_element_by_css_selector(
            'select[name="month_year_of_visit"] option[value="{0}"]'.format(
                self.review_post_data['month_year_of_visit']
            )
        ).click()

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
        self.assertEquals(command.choices_api_url(self.organisation), "{0}comment/{1}?apikey={2}".format(
            settings.NHS_CHOICES_BASE_URL,
            self.organisation.ods_code,
            settings.NHS_CHOICES_API_KEY
        ))

    def test_uses_parent_code_for_gps(self):
        gp_surgery = create_test_organisation_parent({'code': 'GP1'})
        gp = create_test_organisation({'ods_code': 'GPBRANCH1', 'parent': gp_surgery})
        command = PushReviewsCommand()
        self.assertEquals(command.choices_api_url(gp), "{0}comment/{1}?apikey={2}".format(
            settings.NHS_CHOICES_BASE_URL,
            gp.parent.code,
            settings.NHS_CHOICES_API_KEY
        ))

    def test_succesful_post_to_api(self):
        self.mock_api_post_request(202)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNotNone(review.last_sent_to_api)
        self.assertEquals("{0}: Sent review to the Choices API\n".format(review.id), self.stdout.getvalue())

    def test_api_returns_invalid_xml_error(self):
        self.mock_api_post_request(400)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The XML has invalid fields\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_api_key_error(self):
        self.mock_api_post_request(401)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The API key does not have permission\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_posting_id_error(self):
        self.mock_api_post_request(403)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: PostingID is a duplicate\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_nacs_code_error(self):
        self.mock_api_post_request(404)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: The NACS code A111 is not valid\n".format(review.id), self.stderr.getvalue())

    def test_api_returns_generic_error(self):
        self.mock_api_post_request(500)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        review = Review.objects.get(pk=self.review.pk)
        self.assertIsNone(review.last_sent_to_api)
        self.assertEquals("{0}: Server error\n".format(review.id), self.stderr.getvalue())

    def test_skips_empty_organisations(self):
        # Issue #1308 - organisations with reviews that have already been
        # sent but not yet deleted caused the command to immediately return

        # Mark our test review as having been sent
        self.review.last_sent_to_api = timezone.now()
        self.review.save()

        # Create another org with a review which hasn't been sent
        self.second_organisation = create_test_organisation({'ods_code': 'A112'})
        second_review = create_review(self.second_organisation)

        self.mock_api_post_request(202)
        call_command('send_new_reviews_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        expected_output = "No reviews found for {0}\n{1}: Sent review to the Choices API\n".format(self.organisation, second_review.id)

        self.assertEquals(expected_output, self.stdout.getvalue())
        second_review = Review.objects.get(pk=second_review.id)
        self.assertIsNotNone(second_review.last_sent_to_api)


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
        call_command('delete_reviews_sent_to_choices_api', stdout=self.stdout, stderr=self.stderr)
        self.assertEquals(self.organisation.submitted_reviews.count(), 2)


class ReviewsProviderPickerTests(TestCase):

    def setUp(self):
        self.pick_provider_url = reverse('reviews-pick-provider', kwargs={'cobrand': 'choices'})
        self.results_url = "{0}?organisation_type={1}&location={2}".format(self.pick_provider_url, 'gppractices', 'London')

    def test_results_page_exists(self):
        resp = self.client.get(self.results_url)
        self.assertEqual(resp.status_code, 200)

    @override_settings(REVIEW_IGNORE_ORGANISATIONS=[])
    def test_results_page_finds_organisation(self):
        self.included_hospital = create_test_organisation({
            'name': 'Included Hospital',
            'organisation_type': 'hospitals',
            'ods_code': 'XYZ123'
        })
        results_url = "{0}?organisation_type={1}&location={2}".format(self.pick_provider_url, 'hospitals', 'Hospital')
        resp = self.client.get(results_url)
        self.assertContains(resp, self.included_hospital.name, status_code=200)

    @override_settings(REVIEW_IGNORE_ORGANISATIONS=['XYZ123'])
    def test_results_page_does_not_show_excluded_organisation(self):
        self.included_hospital = create_test_organisation({
            'name': 'Included Hospital',
            'organisation_type': 'hospitals',
            'ods_code': 'ABC123'
        })
        self.excluded_hospital = create_test_organisation({
            'name': 'Excluded Hospital',
            'organisation_type': 'hospitals',
            'ods_code': 'XYZ123'
        })
        results_url = "{0}?organisation_type={1}&location={2}".format(self.pick_provider_url, 'hospitals', 'Hospital')
        resp = self.client.get(results_url)
        self.assertNotContains(resp, self.excluded_hospital.name, status_code=200)
        self.assertContains(resp, self.included_hospital.name, status_code=200)

