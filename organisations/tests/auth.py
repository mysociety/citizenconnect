from django.test import TestCase

from organisations import auth
from organisations.auth import user_is_superuser, user_in_group, user_in_groups
from organisations.tests.lib import AuthorizationTestCase

class AuthTests(AuthorizationTestCase):

    def setUp(self):
        super(AuthTests, self).setUp()

    def test_user_is_superuser(self):
        self.assertTrue(user_is_superuser(self.superuser))
        self.assertTrue(user_is_superuser(self.nhs_superuser))

    def test_user_in_group(self):
        self.assertTrue(user_in_group(self.question_answerer, auth.QUESTION_ANSWERERS))
        self.assertFalse(user_in_group(self.question_answerer, auth.PROVIDERS))

    def test_user_in_groups(self):
        example_group_list = [auth.NHS_SUPERUSERS, auth.CASE_HANDLERS]
        self.assertTrue(user_in_groups(self.nhs_superuser, example_group_list))
        self.assertFalse(user_in_groups(self.question_answerer, example_group_list))