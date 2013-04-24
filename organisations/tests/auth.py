import string

from django.test import TestCase

from django.contrib.auth.models import User

from organisations import auth
from organisations.auth import user_is_superuser, user_in_group, user_in_groups, is_valid_username_char, create_unique_username
from organisations.tests.lib import AuthorizationTestCase

class AuthTests(AuthorizationTestCase):

    def setUp(self):
        super(AuthTests, self).setUp()

    def test_user_is_superuser(self):
        self.assertTrue(user_is_superuser(self.superuser))
        self.assertTrue(user_is_superuser(self.nhs_superuser))

    def test_user_in_group(self):
        self.assertTrue(user_in_group(self.case_handler, auth.CASE_HANDLERS))
        self.assertFalse(user_in_group(self.case_handler, auth.PROVIDERS))

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
        username = create_unique_username(self.test_organisation)
        user = User.objects.create_user(username, 'test@example.com', 'password')
        self.assertEqual(username, 'test_organisation')
        for i in range(1,10):
            username = create_unique_username(self.test_organisation)
            self.assertEqual(username, 'test_organisation_{0}'.format(i))
            user = User.objects.create_user(username, 'test@example.com', 'password')
