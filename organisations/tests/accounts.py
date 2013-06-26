from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail

from .lib import create_test_organisation, create_test_organisation_parent, get_reset_url_from_email, AuthorizationTestCase


class BasicAccountTests(TestCase):
    """
    Tests for the accounts stuff in organisations
    """

    def setUp(self):
        # Create a dummy user and organisation
        self.test_trust = create_test_organisation_parent()
        self.test_organisation = create_test_organisation({'parent': self.test_trust})
        self.test_user = User.objects.create_user('Test User', 'user@example.com', 'password')
        self.test_user.save()

        self.test_trust.users.add(self.test_user)
        self.test_trust.save()

        # Useful urls
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.reset_url = reverse('password_reset')
        self.reset_done_url = reverse('password_reset_done')
        self.reset_complete_url = reverse('password_reset_complete')
        self.password_change_url = reverse('password_change')
        self.password_change_done_url = reverse('password_change_done')

        self.weak_password = 'secret'
        self.strong_password = 'aB3$stduthadu'

    def test_login_page_exists(self):
        resp = self.client.get(self.login_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Login")

    def test_user_can_login_and_gets_redirected_if_next_specified(self):
        dashboard_url = reverse('org-parent-dashboard', kwargs={'code':self.test_organisation.parent.code})
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
        confirm_url = reverse('password_reset_confirm', kwargs={'uidb36': uidb36, 'token': token})

        test_weak_passwords = {
            'new_password1': self.weak_password,
            'new_password2': self.weak_password,
        }
        resp = self.client.post(confirm_url, test_weak_passwords)

        self.assertContains(resp, 'Must be 10 characters or more')

        test_strong_passwords = {
            'new_password1': self.strong_password,
            'new_password2': self.strong_password,
        }
        resp = self.client.post(confirm_url, test_strong_passwords)

        self.assertRedirects(resp, self.reset_complete_url)

        self.test_user = User.objects.get(pk=self.test_user.id)
        self.assertTrue(self.test_user.check_password(self.strong_password))

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

        test_weak_passwords = {
            'old_password': 'password',
            'new_password1': self.weak_password,
            'new_password2': self.weak_password,
        }
        resp = self.client.post(self.password_change_url, test_weak_passwords)

        self.assertContains(resp, 'Must be 10 characters or more')

        test_strong_passwords = {
            'old_password': 'password',
            'new_password1': self.strong_password,
            'new_password2': self.strong_password,
        }
        resp = self.client.post(self.password_change_url, test_strong_passwords)

        self.assertRedirects(resp, self.password_change_done_url)

        self.test_user = User.objects.get(pk=self.test_user.id)
        self.assertTrue(self.test_user.check_password(self.strong_password))


class PrivateHomeTests(AuthorizationTestCase):

    def setUp(self):
        super(PrivateHomeTests, self).setUp()
        self.login_url = reverse('login')
        self.private_home_url = reverse('private_home')

    def test_login_required_for_private_home_page(self):
        expected_login_url = '{0}?next={1}'.format(self.login_url, self.private_home_url)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, expected_login_url)

    def test_private_home_view_used(self):
        test_values = {
            'username': self.trust_user.username,
            'password': self.test_password,
        }
        resp = self.client.post(self.login_url, test_values)
        # Can't use assertRedirects to test because the page it should redirect to
        # also redirects on again (as we test later)
        self.assertEqual(resp._headers['location'], ('Location', 'http://testserver' + self.private_home_url))
        self.assertEqual(resp.status_code, 302)

    def test_moderator_goes_to_moderation_homepage(self):
        moderation_url = reverse('moderate-home')
        self.login_as(self.case_handler)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, moderation_url)

    def test_second_tier_moderator_goes_to_second_tier_moderation_homepage(self):
        second_tier_moderation_url = reverse('second-tier-moderate-home')
        self.login_as(self.second_tier_moderator)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, second_tier_moderation_url)

    def test_provider_goes_to_provider_dashboard(self):
        dashboard_url = reverse('org-parent-dashboard', kwargs={'code': self.test_hospital.parent.code})
        self.login_as(self.trust_user)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, dashboard_url)

    def test_superusers_go_to_superuser_page(self):
        pns_url = reverse('private-national-summary')
        for user in self.nhs_superuser, self.superuser:
            self.login_as(user)
            resp = self.client.get(self.private_home_url)
            self.assertRedirects(resp, pns_url)

    def test_everyone_else_goes_to_private_home_page(self):
        # Provider with no organisations
        self.login_as(self.no_trust_user)
        resp = self.client.get(self.private_home_url)
        self.assertEqual(resp.status_code, 200)

    def test_ccg_user_goes_to_ccg_dashboard(self):
        ccg_dashboard_url = reverse('ccg-dashboard', kwargs={'code': self.test_ccg.code})
        self.login_as(self.ccg_user)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, ccg_dashboard_url)

        # If the ccg user has several ccgs they should be shown a list
        self.ccg_user.ccgs.add(self.other_test_ccg)
        resp = self.client.get(self.private_home_url)
        self.assertEqual(resp.status_code, 200)
        for ccg in self.ccg_user.ccgs.all():
            self.assertContains(resp, "CCG dashboard for {0}".format(ccg.name))

    def test_customer_contact_centre_user_goes_to_escalation_dashboard(self):
        escalation_dashboard_url = reverse('escalation-dashboard')
        self.login_as(self.customer_contact_centre_user)
        resp = self.client.get(self.private_home_url)
        self.assertRedirects(resp, escalation_dashboard_url)

