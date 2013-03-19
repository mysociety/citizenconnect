from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail

from .lib import create_test_organisation, get_reset_url_from_email, AuthorizationTestCase

class BasicAccountTests(TestCase):
    """
    Tests for the accounts stuff in organisations
    """

    def setUp(self):
        # Create a dummy user and organisation
        self.test_organisation = create_test_organisation()
        self.test_user = User.objects.create_user('Test User', 'user@example.com', 'password')
        self.test_user.save()

        self.test_organisation.users.add(self.test_user)
        self.test_organisation.save()

        # Useful urls
        self.login_url = '/private/login'
        self.logout_url = '/private/logout'
        self.reset_url = '/private/password-reset'
        self.reset_done_url = '/private/password-reset-done'
        self.reset_confirm_url = '/private/password-reset-confirm'
        self.reset_complete_url = '/private/password-reset-complete'
        self.password_change_url = '/private/password-change'
        self.password_change_done_url = '/private/password-change-done'

    def test_login_page_exists(self):
        resp = self.client.get(self.login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Login")

    def test_user_can_login_and_gets_redirected_if_next_specified(self):
        dashboard_url = reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code})
        test_values = {
            'username': self.test_user.username,
            'password': 'password',
            'next': dashboard_url
        }
        resp = self.client.post(self.login_url, test_values)
        self.assertRedirects(resp, dashboard_url)

        resp = self.client.get(dashboard_url)
        self.assertTrue(resp.context['request'].user.is_authenticated())

    def test_user_can_logout(self):
        logged_in = self.client.login(username=self.test_user.username, password='password')
        self.assertTrue(logged_in)

        resp = self.client.get(self.logout_url)
        self.assertRedirects(resp, '/')

        resp = self.client.get('/')
        self.assertFalse(resp.context['request'].user.is_authenticated())

    def test_password_reset_page_exists(self):
        resp = self.client.get(self.reset_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Password reset")

    def test_password_reset_page_redirects_to_done_page_and_sends_email(self):
        test_values = {
            'email': self.test_user.email
        }
        resp = self.client.post(self.reset_url, test_values)
        self.assertRedirects(resp, self.reset_done_url)

        self.assertEqual(len(mail.outbox), 1)
        reset_email = mail.outbox[0]

        self.assertEqual(reset_email.to, [self.test_user.email])
        self.assertEqual(reset_email.subject, 'Password reset request from Care Connect')
        self.assertTrue('Please go to the following page and choose a new password' in reset_email.body)
        self.assertTrue('/password-reset-confirm/' in reset_email.body)

    def test_password_reset_confirmation_redirects_to_complete_page_and_resets_password(self):
        # Post to the reset form to setup the tokens for our user
        test_values = {
            'email': self.test_user.email
        }
        self.client.post(self.reset_url, test_values)

        # Get the tokens
        uidb36, token = get_reset_url_from_email(mail.outbox[0])

        # Post a new password to the reset form
        confirm_url = '{0}/{1}-{2}'.format(self.reset_confirm_url, uidb36, token)
        test_new_values = {
            'new_password1': 'new_password',
            'new_password2': 'new_password',
        }

        resp = self.client.post(confirm_url, test_new_values)

        self.assertRedirects(resp, self.reset_complete_url)

        self.test_user = User.objects.get(pk=self.test_user.id)
        self.assertTrue(self.test_user.check_password('new_password'))

    def test_password_change_form_exists(self):
        # Login first
        logged_in = self.client.login(username=self.test_user.username, password='password')
        self.assertTrue(logged_in)

        resp = self.client.get(self.password_change_url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Password change")

    def test_password_change_form_redirects_to_done_page_and_changes_password(self):
        # Login first
        logged_in = self.client.login(username=self.test_user.username, password='password')
        self.assertTrue(logged_in)

        test_values = {
            'old_password': 'password',
            'new_password1': 'new_password',
            'new_password2': 'new_password'
        }
        resp = self.client.post(self.password_change_url, test_values)

        self.assertRedirects(resp, self.password_change_done_url)

        self.test_user = User.objects.get(pk=self.test_user.id)
        self.assertTrue(self.test_user.check_password('new_password'))

class LoginRedirectTests(AuthorizationTestCase):

    def setUp(self):
        super(LoginRedirectTests, self).setUp()
        self.login_url = reverse('login')
        self.login_redirect_url = reverse('login_redirect')

    def test_login_redirect_view_used(self):
        test_values = {
            'username': self.provider.username,
            'password': self.test_password,
        }
        resp = self.client.post(self.login_url, test_values)
        # Can't use assertRedirects to test because the page it should redirect to
        # also redirects on again (as we test later)
        self.assertEqual(resp._headers['location'], ('Location', 'http://testserver' + self.login_redirect_url))
        self.assertEqual(resp.status_code, 302)

    def test_moderator_goes_to_moderation_homepage(self):
        moderation_url = reverse('moderate-home')
        self.login_as(self.case_handler)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, moderation_url)

    def test_provider_goes_to_provider_dashboard(self):
        dashboard_url = reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code})
        self.login_as(self.provider)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, dashboard_url)

    def test_nhs_superuser_goes_to_superuser_page(self):
        map_url = reverse('private-map')
        self.login_as(self.nhs_superuser)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, map_url)

    def test_everyone_else_goes_to_home_page(self):
        home_url = reverse('home', kwargs={'cobrand':'choices'})
        # Django superuser
        self.login_as(self.superuser)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, home_url)
        # Provider with no organisations
        self.login_as(self.no_provider)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, home_url)

    def test_login_required_for_redirect_page(self):
        expected_login_url = '{0}?next={1}'.format(self.login_url, self.login_redirect_url)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, expected_login_url)

    def test_multi_provider_user_goes_to_dashboard_choice_page(self):
        pals_url = reverse('dashboard-choice')
        self.login_as(self.pals)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, pals_url)

    def test_question_answerer_goes_to_questions_dashboard(self):
        questions_dashboard_url = reverse('questions-dashboard')
        self.login_as(self.question_answerer)
        resp = self.client.get(self.login_redirect_url)
        self.assertRedirects(resp, questions_dashboard_url)
