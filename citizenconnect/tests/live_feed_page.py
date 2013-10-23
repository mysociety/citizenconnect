from datetime import timedelta

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.conf import settings

from organisations.tests.lib import (
    create_test_problem,
    create_problem_with_age,
    create_review_with_age
)
from reviews_display.tests import create_test_review, create_test_organisation

class LiveFeedTests(TestCase):

    def setUp(self):
        self.live_feed_url = reverse('live-feed', kwargs={'cobrand': 'choices'})
        self.organisation = create_test_organisation({})

    def test_doesnt_show_replies(self):
        review = create_test_review({'organisation': self.organisation})
        reply = create_test_review({'organisation': self.organisation})
        reply.in_reply_to = review
        reply.save()
        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        reply_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': reply.api_posting_id,
                'ods_code': reply.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        resp = self.client.get(self.live_feed_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, reply_url)

    @override_settings(LIVE_FEED_CUTOFF_DAYS=30)
    def test_limits_initial_results(self):
        problem = create_test_problem({'organisation': self.organisation})
        old_problem_date = timezone.now() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS + 1)
        old_problem = create_test_problem({
            'organisation': self.organisation,
            'created': old_problem_date
        })

        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, reverse(
                'problem-view',
                kwargs={'pk': problem.id, 'cobrand': 'choices'}
            )
        )
        self.assertNotContains(resp, reverse(
                'problem-view',
                kwargs={'pk': old_problem.id, 'cobrand': 'choices'}
            )
        )

    @override_settings(LIVE_FEED_CUTOFF_DAYS=2)
    def test_filters_by_date_range(self):
        # Make some test problems with varying dates
        problem = create_test_problem({'organisation': self.organisation})
        review = create_test_review({'organisation': self.organisation})

        now = timezone.now()

        old_problem = create_problem_with_age(self.organisation, 1)
        old_review = create_review_with_age(self.organisation, 1)
        older_problem = create_problem_with_age(self.organisation, 3)
        older_review = create_review_with_age(self.organisation, 3)

        # Get the urls for each, because that's the easiest bit of content to
        # look for in the page to see if they're filtered or not
        problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'choices'})
        old_problem_url = reverse('problem-view', kwargs={'pk': old_problem.id, 'cobrand': 'choices'})
        older_problem_url = reverse('problem-view', kwargs={'pk': older_problem.id, 'cobrand': 'choices'})
        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        old_review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': old_review.api_posting_id,
                'ods_code': old_review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        older_review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': older_review.api_posting_id,
                'ods_code': older_review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )

        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, old_problem_url)
        self.assertContains(resp, review_url)
        self.assertContains(resp, old_review_url)
        # LIVE_FEED_CUTOFF_DAYS should exclude this until we expand the date
        # range
        self.assertNotContains(resp, older_problem_url)
        self.assertNotContains(resp, older_review_url)

        # Extending the date range to four days should bring all the problems
        # in
        four_days_ago = now - timedelta(days=4)

        filtered_url_string = "{0}?start_day={1}&start_month={2}&start_year={3}&end_day={4}&end_month={5}&end_year={6}"
        filtered_url = filtered_url_string.format(
            self.live_feed_url,
            four_days_ago.day,
            four_days_ago.month,
            four_days_ago.year,
            now.day,
            now.month,
            now.year
        )

        resp = self.client.get(filtered_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, old_problem_url)
        self.assertContains(resp, older_problem_url)
        self.assertContains(resp, review_url)
        self.assertContains(resp, old_review_url)
        self.assertContains(resp, older_review_url)

        # Contracting the date range to 1 day should limit the problems again
        filtered_url = filtered_url_string.format(
            self.live_feed_url,
            now.day,
            now.month,
            now.year,
            now.day,
            now.month,
            now.year
        )

        resp = self.client.get(filtered_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, old_problem_url)
        self.assertNotContains(resp, older_problem_url)
        self.assertNotContains(resp, old_review_url)
        self.assertNotContains(resp, older_review_url)

    def test_date_filters_show_defaults(self):
        pass

    def test_filters_by_organisation(self):
        pass

    def test_shows_open_and_closed_problems(self):
        pass

    def test_shows_unmoderated_problems(self):
        pass

    def test_doesnt_show_requiring_second_tier_moderation_problems(self):
        pass

    def test_pagination(self):
        pass
