import string

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from organisations import auth
from organisations.auth import (user_is_superuser,
                                user_in_group,
                                user_in_groups,
                                is_valid_username_char,
                                create_unique_username,
                                create_initial_password,
                                create_home_links_for_user)
from organisations.tests.lib import AuthorizationTestCase


class AuthTests(AuthorizationTestCase):

    def setUp(self):
        super(AuthTests, self).setUp()

    def test_user_is_superuser(self):
        self.assertTrue(user_is_superuser(self.superuser))
        self.assertTrue(user_is_superuser(self.nhs_superuser))

    def test_user_in_group(self):
        self.assertTrue(user_in_group(self.case_handler, auth.CASE_HANDLERS))
        self.assertFalse(user_in_group(self.case_handler, auth.ORGANISATION_PARENTS))

    def test_user_in_groups(self):
        example_group_list = [auth.NHS_SUPERUSERS, auth.CASE_HANDLERS]
        self.assertTrue(user_in_groups(self.nhs_superuser, example_group_list))
        self.assertFalse(user_in_groups(self.ccg_user, example_group_list))

    def test_is_valid_username_char(self):
        for char in string.whitespace:
            self.assertFalse(is_valid_username_char(char))

        for char in string.punctuation:
            if char != '_':
                self.assertFalse(is_valid_username_char(char))

        for char in string.digits:
            self.assertFalse(is_valid_username_char(char))

        for char in string.ascii_letters:
            self.assertTrue(is_valid_username_char(char))

        self.assertTrue(is_valid_username_char('_'))

    def test_create_unique_username(self):
        username = create_unique_username(self.test_hospital)
        User.objects.create_user(username, 'test@example.com', 'password')
        self.assertEqual(username, 'test_organisation')

        for i in range(1, 10):
            username = create_unique_username(self.test_hospital)
            self.assertEqual(username, 'test_organisation_{0}'.format(i))
            User.objects.create_user(username, 'test@example.com', 'password')

        # Now make the organisation name far too long and test that the code can handle that too.
        self.test_hospital.name = 'This is a name that is far longer than expected but who knows it might happen'
        username = create_unique_username(self.test_hospital)
        User.objects.create_user(username, 'test@example.com', 'password')
        self.assertEqual(username, 'this_is_a_name_that_is_far_lon')
        for i in range(1, 10):
            username = create_unique_username(self.test_hospital)
            User.objects.create_user(username, 'test@example.com', 'password')
            self.assertEqual(username, 'this_is_a_name_that_is_far_l_{0}'.format(i))
            self.assertTrue(len(username) <= 30)

        for i in range(10, 20):
            username = create_unique_username(self.test_hospital)
            User.objects.create_user(username, 'test@example.com', 'password')
            self.assertEqual(username, 'this_is_a_name_that_is_far_{0}'.format(i))
            self.assertTrue(len(username) <= 30)

    def test_create_initial_password(self):
        seen_passwords = set()

        for i in range(100):
            password = create_initial_password()

            # check it is long
            self.assertEqual(len(password), 60)

            # check it is unique (ie has not been seen before)
            self.assertFalse(password in seen_passwords)
            seen_passwords.add(password)

    def test_create_home_links_for_user(self):

        tests = [
            (
                self.trust_user,
                [
                    {
                        'title': 'Dashboard for Test Trust',
                        'url': reverse('org-parent-dashboard', kwargs={'code': 'TRUST1'})
                    },
                ]
            ),
            (
                self.superuser,
                [
                    {
                        'title': 'Superuser Dashboard',
                        'url': reverse('superuser-dashboard')
                    },
                ]
            ),
            (
                self.anonymous_user,
                []
            ),
            (
                self.no_trust_user,
                []
            ),
            (
                self.gp_surgery_user,
                [
                    {
                        'title': 'Dashboard for other test trust',
                        'url': reverse('org-parent-dashboard', kwargs={'code': 'XYZ'})
                    },
                ]
            ),
            (
                self.nhs_superuser,
                [
                    {
                        'title': 'Superuser Dashboard',
                        'url': reverse('superuser-dashboard')
                    },
                ]
            ),
            (
                self.case_handler,
                [
                    {
                        'title': 'Moderation home',
                        'url': reverse('moderate-home')
                    },
                ]
            ),
            (
                self.second_tier_moderator,
                [
                    {
                        'title': 'Second tier moderation home',
                        'url': reverse('second-tier-moderate-home')
                    },
                ]
            ),
            (
                self.no_ccg_user,
                []
            ),
            (
                self.ccg_user,
                [
                    {
                        'title': 'CCG dashboard for Test CCG',
                        'url': reverse('ccg-dashboard', kwargs={'code': 'CCG1'})
                    },
                ]
            ),
            (
                self.customer_contact_centre_user,
                []
            ),
        ]

        for user, expected_links in tests:
            links = create_home_links_for_user(user)
            self.assertEqual(
                expected_links,
                links,
                "Did not get expected links for '{0}' user, got: {1}, expected: {2}".format(user, links, expected_links)
            )
