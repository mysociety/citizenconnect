import datetime

from django.test import TestCase
from django.core import mail
from django.contrib.gis.geos import Point
from django.utils.timezone import utc
from django.core.exceptions import ValidationError

from .lib import (create_test_organisation,
                  create_test_ccg,
                  create_test_organisation_parent,
                  create_test_problem,
                  AuthorizationTestCase)

from ..models import (Organisation,
                      OrganisationParent,
                      CCG)


class OrganisationParentModelTests(TestCase):

    def setUp(self):
        # create a trust
        self.test_trust = create_test_organisation_parent({'code': 'MYTRUST'})

        # create three orgs, two of which belong to the trust, and one that does not
        self.test_trust_org_1 = create_test_organisation({"parent": self.test_trust, "ods_code": "test1"})
        self.test_trust_org_2 = create_test_organisation({"parent": self.test_trust, "ods_code": "test2"})
        self.test_other_org = create_test_organisation({"ods_code": "other"})

        # create a problem in each org
        for org in Organisation.objects.all():
            create_test_problem({
                'organisation': org,
                'description': "Problem with '{0}'".format(org.parent.code),
            })

    def test_trust_problem_set(self):
        # check that the right problems are found using the problem_set
        problems = self.test_trust.problem_set.order_by('description')
        self.assertEqual(problems.count(), 2)
        for p in problems:
            self.assertEqual(p.organisation.parent, self.test_trust)

    def test_escalation_ccg_always_in_ccgs(self):
        ccg = create_test_ccg({})
        trust = OrganisationParent(name="test_trust",
                                   code="ABC",
                                   choices_id=12345,
                                   email='test-trust@example.org',
                                   secondary_email='test-trust-secondary@example.org',
                                   escalation_ccg=ccg)

        trust.save()
        trust = OrganisationParent.objects.get(pk=trust.id)
        self.assertTrue(trust.escalation_ccg in trust.ccgs.all())


class CCGModelTests(TestCase):

    def setUp(self):
        # create a ccg
        self.test_ccg = create_test_ccg({'code': 'CCG1'})

        # create a trust
        self.test_trust = create_test_organisation_parent({'code': 'MYTRUST', 'escalation_ccg': self.test_ccg})

        # create three orgs, two of which belong to the ccg, and one that does not
        self.test_trust_org_1 = create_test_organisation({"parent": self.test_trust, "ods_code": "test1"})
        self.test_trust_org_2 = create_test_organisation({"parent": self.test_trust, "ods_code": "test2"})
        self.test_other_org = create_test_organisation({"ods_code": "other"})

        # create a problem in each org
        for org in Organisation.objects.all():
            create_test_problem({
                'organisation': org,
                'description': "Problem with '{0}'".format(org.parent.code),
            })

    def test_ccg_problem_set(self):
        # check that the right problems are found using the problem_set
        problems = self.test_ccg.problem_set.order_by('description')
        self.assertEqual(problems.count(), 2)
        for p in problems:
            self.assertEqual(p.organisation.parent.ccgs.all()[0], self.test_ccg)

    def test_that_email_address_is_required(self):
        self.assertRaises(ValidationError, CCG.objects.create, code="NOEMAIL")
        self.assertRaises(ValidationError, CCG.objects.create, email="", code="NOEMAIL")


class CCGModelAuthTests(AuthorizationTestCase):

    def setUp(self):
        super(CCGModelAuthTests, self).setUp()

    def test_allowed_users_can_access_ccg(self):
        self.assertTrue(self.test_ccg.can_be_accessed_by(self.ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_ccg.can_be_accessed_by(user))

    def test_disallowed_users_cannot_access_ccg(self):
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.trust_user))
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.gp_surgery_user))
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.no_trust_user))
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.other_ccg_user))
        self.assertFalse(self.other_test_ccg.can_be_accessed_by(self.ccg_user))
        self.assertFalse(self.test_ccg.can_be_accessed_by(self.no_ccg_user))


class OrganisationParentModelTests(TestCase):
    def test_that_email_address_is_required(self):
        self.assertRaises(
            ValidationError,
            OrganisationParent.objects.create,
            escalation_ccg=create_test_ccg({}),
            choices_id=123
        )
    def test_that_email_address_is_required(self):
        self.assertRaises(
            ValidationError,
            OrganisationParent.objects.create,
            escalation_ccg=create_test_ccg({}),
            choices_id=123,
            email=""
        )


class OrganisationModelTests(TestCase):
    def test_organisation_type_name(self):
        test_org = create_test_organisation({'organisation_type': 'hospitals'})
        self.assertEqual(test_org.organisation_type_name, 'Hospital')


class OrganisationModelAuthTests(AuthorizationTestCase):

    def setUp(self):
        super(OrganisationModelAuthTests, self).setUp()

    def test_user_can_access_provider_happy_path(self):
        self.assertTrue(self.test_hospital.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_gp_branch.can_be_accessed_by(self.gp_surgery_user))

    def test_superusers_can_access_any_provider(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_hospital.can_be_accessed_by(user))
            self.assertTrue(self.test_gp_branch.can_be_accessed_by(user))

    def test_anon_user_cannot_access_any_provider(self):
        self.assertFalse(self.test_hospital.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.test_gp_branch.can_be_accessed_by(self.anonymous_user))

    def test_user_with_no_orgs_cannot_access_organisation(self):
        self.assertFalse(self.test_hospital.can_be_accessed_by(self.no_trust_user))
        self.assertFalse(self.test_gp_branch.can_be_accessed_by(self.no_trust_user))

    def test_user_with_other_org_cannot_access_different_org(self):
        self.assertFalse(self.test_hospital.can_be_accessed_by(self.gp_surgery_user))
        self.assertFalse(self.test_gp_branch.can_be_accessed_by(self.trust_user))

    def test_user_with_no_ccgs_cannot_access_orgs(self):
        self.assertFalse(self.test_hospital.can_be_accessed_by(self.no_ccg_user))
        self.assertFalse(self.test_gp_branch.can_be_accessed_by(self.no_ccg_user))

    def test_user_with_other_ccg_cannot_access_org_with_no_ccg(self):
        self.assertFalse(self.test_hospital.can_be_accessed_by(self.other_ccg_user))
        self.assertFalse(self.test_gp_branch.can_be_accessed_by(self.ccg_user))

    def test_user_with_ccg_can_access_ccg_org(self):
        self.assertTrue(self.test_hospital.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.test_gp_branch.can_be_accessed_by(self.other_ccg_user))


class OrganisationMetaphoneTests(TestCase):

    def setUp(self):
        # Make an organisation without saving it

        trust = create_test_organisation_parent()
        self.organisation = Organisation(name=u'Test Organisation',
                                         organisation_type='gppractices',
                                         choices_id='12702',
                                         ods_code='F84021',
                                         point=Point(51.536, -0.06213),
                                         parent=trust)

    def test_name_metaphone_created_on_save(self):
        self.assertEqual(self.organisation.name_metaphone, '')
        self.organisation.save()
        self.assertEqual(self.organisation.name_metaphone, 'TSTRKNSXN')


class CreateTestOrganisationParentMixin(object):
    ods_counter = 0

    def create_test_object(self, attributes={}):
        attributes['code'] = 'F{0}'.format(self.ods_counter)
        self.ods_counter += 1
        return create_test_organisation_parent(attributes)


class CreateTestCCGMixin(object):
    ccg_code_counter = 0

    def create_test_object(self, attributes={}):
        attributes['code'] = 'CCG{0}'.format(self.ccg_code_counter)
        self.ccg_code_counter += 1
        return create_test_ccg(attributes)


class SendMailTestsMixin(object):

    def setUp(self):
        self.test_object = self.create_test_object({"email": "foo@example.com"})

    def test_send_mail_raises_if_recipient_list_provided(self):
        test_object = self.test_object
        self.assertRaises(TypeError, test_object.send_mail, subject="Test Subject", message="Test message", recipient_list="bob@foo.com")

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


# This is a bit convoluted. We want to test the email sending for the
# Organisations and the CCGs. Use this matrix of mixins to do all the tests
# without any code repetition.

class OrganisationParentModelSendMailTests(CreateTestOrganisationParentMixin, SendMailTestsMixin, TestCase):
    pass


class CCGModelSendMailTests(CreateTestCCGMixin, SendMailTestsMixin, TestCase):
    pass
