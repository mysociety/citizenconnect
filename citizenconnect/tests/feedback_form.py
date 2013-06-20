from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core import mail

from organisations.tests.lib import create_test_problem


class FeedbackFormTest(TestCase):
    def setUp(self):
        self.feedback_form_url = reverse('feedback', kwargs={'cobrand': 'choices'})
        self.feedback_confirm_url = reverse('feedback-confirm', kwargs={'cobrand': 'choices'})

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
        problem = create_test_problem()
        resp = self.client.get(self.feedback_form_url + '?problem_id={0}'.format(problem.id))
        self.assertContains(resp, "RE: Problem reference {0}".format(problem.id))

    def test_feedback_form_doesnt_reference_problem_by_default(self):
        resp = self.client.get(self.feedback_form_url)
        self.assertNotContains(resp, "RE: Problem")
