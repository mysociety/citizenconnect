from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail

from .lib import create_test_organisation, get_reset_url_from_email, AuthorizationTestCase

class OrganisationModelTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationModelTests, self).setUp()

    def test_user_can_access_provider_happy_path(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.test_allowed_user))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.test_other_provider_user))

    def test_superusers_can_access_any_provider(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_organisation.can_be_accessed_by(user))
            self.assertTrue(self.other_test_organisation.can_be_accessed_by(user))

    def test_anon_user_cannot_access_any_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.anonymous_user))

    def test_user_with_no_providers_cannot_access_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.test_no_provider_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.test_no_provider_user))

    def test_user_with_other_provider_cannot_access_different_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.test_other_provider_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.test_allowed_user))

    def test_pals_user_can_access_both_providers(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.test_pals_user))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.test_pals_user))