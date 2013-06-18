from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import auth

from .models import FailedAttempt
from .exceptions import LoginBlockedError


class FailedLoginBlockerTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user('test_user', 'test@example.com', 'password')
        self.login_url = reverse('login')

    def test_blocked_after_three_failed_login_attempts(self):
        credentials = {
            'username': self.test_user.username,
            'password': 'wrong_password',
        }

        self.client.login(**credentials)
        failed_attempt = FailedAttempt.objects.all()[0]
        self.assertEqual(self.test_user.username, failed_attempt.username)
        self.assertEqual(1, failed_attempt.failures)

        self.client.login(**credentials)
        failed_attempt = FailedAttempt.objects.all()[0]
        self.assertEqual(2, failed_attempt.failures)

        self.client.login(**credentials)
        failed_attempt = FailedAttempt.objects.all()[0]
        self.assertEqual(3, failed_attempt.failures)

        # After 3 failed login attempts, an exception should be raised.
        self.assertRaises(LoginBlockedError, self.client.login, **credentials)
