import datetime

from django.test import TestCase
from django.core import mail
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point
from django.utils.timezone import utc

from .lib import (create_test_organisation,
                  create_test_ccg,
                  create_test_trust,
                  create_test_problem,
                  AuthorizationTestCase)

from ..models import Organisation


class TrustModelTests(TestCase):

    def setUp(self):
        # create a trust
        self.test_trust = create_test_trust({'code': 'MYTRUST'})

        # create three orgs, two of which belong to the trust, and one that does not
        self.test_trust_org_1 = create_test_organisation({"trust": self.test_trust, "ods_code": "test1"})
        self.test_trust_org_2 = create_test_organisation({"trust": self.test_trust, "ods_code": "test2"})
        self.test_other_org = create_test_organisation({"ods_code": "other"})

        # create a problem in each org
        for org in Organisation.objects.all():
            create_test_problem({
                'organisation': org,
                'description': "Problem with '{0}'".format(org.trust.code),
            })

    def test_trust_problem_set(self):
        # check that the right problems are found using the problem_set
        problems = self.test_trust.problem_set.order_by('description')
        self.assertEqual(problems.count(), 2)
        for p in problems:
            self.assertEqual( p.organisation.trust, self.test_trust)


class OrganisationModelTests(TestCase):
    def test_organisation_type_name(self):
        test_org = create_test_organisation({'organisation_type': 'hospitals'})
        self.assertEqual(test_org.organisation_type_name, 'Hospital')


class OrganisationModelAuthTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationModelAuthTests, self).setUp()

    def test_user_can_access_provider_happy_path(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.other_provider))

    def test_superusers_can_access_any_provider(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_organisation.can_be_accessed_by(user))
            self.assertTrue(self.other_test_organisation.can_be_accessed_by(user))

    def test_anon_user_cannot_access_any_provider(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.anonymous_user))

    def test_user_with_no_orgs_cannot_access_organisation(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.no_provider))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.no_provider))

    def test_user_with_other_org_cannot_access_different_org(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.other_provider))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.trust_user))

    def test_user_with_no_ccgs_cannot_access_orgs(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.no_ccg_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.no_ccg_user))

    def test_user_with_other_ccg_cannot_access_org_with_no_ccg(self):
        self.assertFalse(self.test_organisation.can_be_accessed_by(self.other_ccg_user))
        self.assertFalse(self.other_test_organisation.can_be_accessed_by(self.ccg_user))

    def test_user_with_ccg_can_access_ccg_org(self):
        self.assertTrue(self.test_organisation.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.other_test_organisation.can_be_accessed_by(self.other_ccg_user))


class OrganisationMetaphoneTests(TestCase):

    def setUp(self):
        # Make an organisation without saving it

        trust = create_test_trust()
        self.organisation = Organisation(name=u'Test Organisation',
                                         organisation_type='gppractices',
                                         choices_id='12702',
                                         ods_code='F84021',
                                         point=Point(51.536, -0.06213),
                                         trust=trust)

    def test_name_metaphone_created_on_save(self):
        self.assertEqual(self.organisation.name_metaphone, '')
        self.organisation.save()
        self.assertEqual(self.organisation.name_metaphone, 'TSTRKNSXN')


class CreateTestTrustMixin(object):
    ods_counter = 0

    def create_test_object(self, attributes={}):
        attributes['code'] = 'F{0}'.format(self.ods_counter)
        self.ods_counter += 1
        return create_test_trust(attributes)


class CreateTestCCGMixin(object):
    ccg_code_counter = 0

    def create_test_object(self, attributes={}):
        attributes['code'] = 'CCG{0}'.format(self.ccg_code_counter)
        self.ccg_code_counter += 1
        return create_test_ccg(attributes)


class UserCreationTestsMixin(object):

    def setUp(self):
        # create users needed for tests
        self.user_foo = User.objects.create_user("foo", email="foo@example.com")

        # create organisations needed for tests
        self.test_object_no_email = self.create_test_object({'name': "No Email", 'email': ""})  # ISSUE-329
        self.test_object_no_user = self.create_test_object({'name': "No User", 'email': "no-email@example.com"})
        self.test_object_foo_with_user = self.create_test_object({'name': "Foo with User", 'email': "foo@example.com"})
        self.test_object_foo_no_user = self.create_test_object({'name': "Foo without User", 'email': "foo@example.com"})

        # add the user to test_object_foo_with_user
        self.test_object_foo_with_user.users.add(self.user_foo)

    def test_user_creation_where_test_object_has_no_email(self):  # ISSUE-329
        test_object = self.test_object_no_email

        self.assertEqual(test_object.users.count(), 0)
        self.assertRaises(ValueError, lambda: test_object.ensure_related_user_exists())
        self.assertEqual(test_object.users.count(), 0)

    def test_user_creation_where_user_exists(self):
        test_object = self.test_object_foo_with_user

        self.assertEqual(test_object.users.count(), 1)
        test_object.ensure_related_user_exists()
        self.assertEqual(test_object.users.count(), 1)

    def test_user_creation_where_user_missing(self):
        test_object = self.test_object_no_user

        self.assertEqual(test_object.users.count(), 0)
        test_object.ensure_related_user_exists()
        self.assertEqual(test_object.users.count(), 1)

        # test that password _is_ usable - if it is not usable then the password
        # cannot be reset. See #689
        user = test_object.users.all()[0]
        self.assertTrue(user.has_usable_password())
        self.assertEqual(user.email, test_object.email)

    def test_user_creation_where_user_exists_but_not_related(self):
        test_object = self.test_object_foo_no_user

        self.assertEqual(test_object.users.count(), 0)
        test_object.ensure_related_user_exists()
        self.assertEqual(test_object.users.count(), 1)

        self.assertEqual(test_object.users.all()[0].id, self.user_foo.id)


class SendMailTestsMixin(object):

    def setUp(self):
        self.test_object = self.create_test_object({"email": "foo@example.com"})

    def test_send_mail_raises_if_no_email_on_test_object(self):
        # Remove this test once ISSUE-329 resolved
        test_object = self.create_test_object({"email": ""})
        self.assertRaises(ValueError, test_object.send_mail, subject="Test Subject", message="Test message")

    def test_send_mail_raises_if_recipient_list_provided(self):
        test_object = self.test_object
        self.assertRaises(TypeError, test_object.send_mail, subject="Test Subject", message="Test message", recipient_list="bob@foo.com")

    def test_send_mail_creates_user(self):
        test_object = self.test_object

        self.assertEqual(test_object.users.count(), 0)
        test_object.send_mail('test', 'foo')
        self.assertEqual(test_object.users.count(), 1)

    def test_send_mail_that_the_intro_email_is_sent(self):
        test_object = self.test_object

        self.assertFalse(test_object.intro_email_sent)
        test_object.send_mail('test', 'foo')
        self.assertTrue(test_object.intro_email_sent)

        self.assertEqual(len(mail.outbox), 2)
        intro_mail = mail.outbox[0]
        trigger_mail = mail.outbox[1]

        self.assertTrue(test_object.users.all()[0].username in intro_mail.body)
        self.assertTrue(test_object.email in intro_mail.to)

        self.assertEqual(trigger_mail.subject, 'test')
        self.assertEqual(trigger_mail.body,    'foo')

        # print
        # print intro_mail.subject
        # print intro_mail.body

    def test_send_mail_intro_email_not_sent_twice(self):
        test_object = self.test_object
        now = datetime.datetime.utcnow().replace(tzinfo=utc)

        test_object.intro_email_sent = now
        test_object.save()

        self.assertEqual(test_object.intro_email_sent, now)
        test_object.send_mail('test', 'foo')
        self.assertEqual(test_object.intro_email_sent, now)

        self.assertEqual(len(mail.outbox), 1)
        trigger_mail = mail.outbox[0]

        self.assertEqual(trigger_mail.subject, 'test')
        self.assertEqual(trigger_mail.body, 'foo')


# This is a bit convoluted. We want to test the user creation and email sending
# for the Organisations and the CCGs. Use this matrix of mixins to do all the
# tests without any code repetition.
class TrustModelUserCreationTests(CreateTestTrustMixin, UserCreationTestsMixin, TestCase):
    pass


class CCGModelUserCreationTests(CreateTestCCGMixin, UserCreationTestsMixin, TestCase):
    pass


class TrustModelSendMailTests(CreateTestTrustMixin, SendMailTestsMixin, TestCase):
    pass


class CCGModelSendMailTests(CreateTestCCGMixin, SendMailTestsMixin, TestCase):
    pass
