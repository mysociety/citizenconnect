from django.test import TestCase

from django.core.urlresolvers import reverse

from reviews_display.tests import create_test_review, create_test_organisation

class HomepageTests(TestCase):

    def setUp(self):
        self.homepage_url = reverse('home', kwargs={'cobrand': 'choices'})

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
        resp = self.client.get(self.homepage_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, reply_url)
