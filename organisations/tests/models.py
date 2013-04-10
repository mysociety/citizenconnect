import unittest

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core import mail
from django.contrib.auth.models import User

from .lib import create_test_organisation, get_reset_url_from_email, AuthorizationTestCase

from ..models import Organisation

class OrganisationModelAuthTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationModelAuthTests, self).setUp()

    def test_user_can_access_provider_happy_path(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.provider))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.other_provider))

    def test_superusers_can_access_any_provider(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_organisation.can_be_accessed_by(user))
            self.assertTrue(self.other_test_organisation.can_be_accessed_by(user))

    def test_anon_user_cannot_access_any_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.anonymous_user))

    def test_user_with_no_providers_cannot_access_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.no_provider))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.no_provider))

    def test_user_with_other_provider_cannot_access_different_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.other_provider))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.provider))

    def test_pals_user_can_access_both_providers(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.pals))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.pals))

    def test_user_with_no_ccgs_cannot_access_providers(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.no_ccg))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.no_ccg))

    def test_user_with_other_ccg_cannot_access_provider_with_no_ccg(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.other_ccg_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.ccg_user))

    def test_user_with_ccg_can_access_ccg_provider(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.other_ccg_user))



class OrganisationModelUserCreationTests(TestCase):

    def setUp(self):
        # create users needed for tests
        self.user_foo = User.objects.create_user("foo", email="foo@example.com")

        # create organisations needed for tests
        self.org_no_email      = create_test_organisation({'ods_code': 'F1', 'name': "No Email"}) # ISSUE-329
        self.org_no_user       = create_test_organisation({'ods_code': 'F2', 'name': "No User",          'email': "no-email@example.com"})
        self.org_foo_with_user = create_test_organisation({'ods_code': 'F3', 'name': "Foo with User",    'email': "foo@example.com"})
        self.org_foo_no_user   = create_test_organisation({'ods_code': 'F4', 'name': "Foo without User", 'email': "foo@example.com"})

        # add the user to org_foo_with_user
        self.org_foo_with_user.users.add( self.user_foo )

    def test_user_creation_where_org_has_no_email(self): # ISSUE-329
        org = self.org_no_email
        
        self.assertEqual(org.users.count(), 0)
        self.assertRaises(ValueError, lambda: org.ensure_related_user_exists() )
        self.assertEqual(org.users.count(), 0)
        
    def test_user_creation_where_user_exists(self):
        org = self.org_foo_with_user

        self.assertEqual(org.users.count(), 1)
        org.ensure_related_user_exists()
        self.assertEqual(org.users.count(), 1)

    def test_user_creation_where_user_missing(self):
        org = self.org_no_user

        self.assertEqual(org.users.count(), 0)
        org.ensure_related_user_exists()
        self.assertEqual(org.users.count(), 1)

        # test that password is not usable
        user = org.users.all()[0]
        self.assertFalse( user.has_usable_password() )
        self.assertEqual( user.email, org.email )
        
    def test_user_creation_where_user_exists_but_not_related(self):
        org = self.org_foo_no_user

        self.assertEqual(org.users.count(), 0)
        org.ensure_related_user_exists()
        self.assertEqual(org.users.count(), 1)

        self.assertEqual(org.users.all()[0].id, self.user_foo.id)
