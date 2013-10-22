from django.test import TestCase

from django.core.urlresolvers import reverse

from reviews_display.tests import create_test_review, create_test_organisation

class LiveFeedTests(TestCase):

    def setUp(self):
        self.live_feed_url = reverse('live-feed', kwargs={'cobrand': 'choices'})

    def test_doesnt_show_replies(self):
        organisation = create_test_organisation({})
        review = create_test_review({'organisation': organisation})
        reply = create_test_review({'organisation': organisation})
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

    def test_limits_initial_results(self):
        pass

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
