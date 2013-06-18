from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class FailedLoginBlockerTest(TestCase):
    def setUp(self):
        self.test_user = User.objects.create_user('test_user', 'test@example.com', 'password')
        self.login_url = reverse('login')

    def test_blocked_after_three_failed_login_attempts(self):
        login_params = {
            'username': self.test_user.username,
            'password': 'wrong_password',
        }
        resp = self.client.post(self.login_url, login_params)
        self.assertEqual(200, resp.status_code)

        resp = self.client.post(self.login_url, login_params)
        self.assertEqual(200, resp.status_code)

        resp = self.client.post(self.login_url, login_params)
        self.assertEqual(200, resp.status_code)

        resp = self.client.post(self.login_url, login_params)
        self.assertEqual(403, resp.status_code)
