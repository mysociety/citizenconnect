from datetime import datetime, timedelta

from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import utc
from django.core.urlresolvers import reverse
from django.conf import settings

from organisations.tests.lib import create_test_problem
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
        old_problem_date = datetime.utcnow() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS + 1)
        old_problem_date = old_problem_date.replace(tzinfo=utc)
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

    def test_filters_by_date_range(self):
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
