from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import mail

from organisations.tests.lib import create_test_problem


class FeedbackFormTest(TestCase):
    def setUp(self):
        self.feedback_form_url = reverse('feedback', kwargs={'cobrand': 'choices'})
        self.feedback_confirm_url = reverse('feedback-confirm', kwargs={'cobrand': 'choices'})
        self.test_problem = create_test_problem({})

    def test_feedback_form_exists(self):
        resp = self.client.get(self.feedback_form_url)
        self.assertEquals(200, resp.status_code)

    def test_posting_feedback(self):
        resp = self.client.post(self.feedback_form_url, {'name': 'Bob', 'email': 'bob@example.com', 'feedback_comments': 'Test XYZ Comment'})
        self.assertEquals(302, resp.status_code)
        self.assertRedirects(resp, self.feedback_confirm_url)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue('Test XYZ Comment' in email.body)
        self.assertEqual(email.to, [settings.FEEDBACK_EMAIL_ADDRESS])
        self.assertEqual(email.subject, 'Feedback on CareConnect Service from Bob')

    def test_missing_data(self):
        resp = self.client.post(self.feedback_form_url, {'name': 'Bob', 'email': '', 'feedback_comments': 'Test'})
        self.assertEquals(200, resp.status_code)
        self.assertContains(resp, "This field is required")
        self.assertEqual(len(mail.outbox), 0)

    def test_report_problem_as_unsuitable(self):
        resp = self.client.get(self.feedback_form_url + '?problem_ref=' + self.test_problem.reference_number)
        self.assertContains(resp, 'RE: Problem reference ' + self.test_problem.reference_number)

    def test_report_problem_as_unsuitable_where_problem_not_in_db(self):
        resp = self.client.get(self.feedback_form_url + '?problem_ref=P9999')
        self.assertNotContains(resp, "RE: Problem reference")

    def test_feedback_form_doesnt_reference_problem_by_default(self):
        resp = self.client.get(self.feedback_form_url)
        self.assertNotContains(resp, "RE: Problem reference")

    def test_handles_unicode(self):
        resp = self.client.post(self.feedback_form_url, {
            'name': u'Bob \u2019',
            'email': 'bob@example.com',
            'feedback_comments': u'Test XYZ Comment \u2019'})
        self.assertEquals(302, resp.status_code)
        self.assertRedirects(resp, self.feedback_confirm_url)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertTrue(u'Test XYZ Comment \u2019' in email.body)
        self.assertEqual(email.subject, u'Feedback on CareConnect Service from Bob \u2019')
