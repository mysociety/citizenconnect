from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse


class FeedbackFormTest(TestCase):
    def setUp(self):
        self.feedback_form_url = reverse('feedback', kwargs={'cobrand': 'choices'})
        self.feedback_confirm_url = reverse('feedback-confirm', kwargs={'cobrand': 'choices'})

    def test_feedback_form_exists(self):
        resp = self.client.get(self.feedback_form_url)
        self.assertEquals(200, resp.status_code)

    def test_posting_feedback(self):
        resp = self.client.post(self.feedback_form_url, {'name': 'Bob', 'email': 'bob@example.com', 'feedback_comments': 'Test'})
        self.assertEquals(302, resp.status_code)
        self.assertRedirects(resp, self.feedback_confirm_url)

    def test_missing_data(self):
        resp = self.client.post(self.feedback_form_url, {'name': 'Bob', 'email': '', 'feedback_comments': 'Test'})
        self.assertEquals(200, resp.status_code)
        self.assertContains(resp, "This field is required")
