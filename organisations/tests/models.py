import datetime
import os

from django.test import TestCase, TransactionTestCase
from django.core import mail
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from django.utils.timezone import utc
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction

from .lib import (create_test_organisation,
                  create_test_ccg,
                  create_test_organisation_parent,
                  create_test_problem,
                  AuthorizationTestCase)

from ..models import (
    Organisation,
    OrganisationParent,
    CCG,
    FriendsAndFamilySurvey
)


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

    def test_primary_ccg_always_in_ccgs(self):
        ccg = create_test_ccg({})
        trust = OrganisationParent(name="test_trust",
                                   code="ABC",
                                   choices_id=12345,
                                   email='test-trust@example.org',
                                   secondary_email='test-trust-secondary@example.org',
                                   primary_ccg=ccg)

        trust.save()
        trust = OrganisationParent.objects.get(pk=trust.id)
        self.assertTrue(trust.primary_ccg in trust.ccgs.all())

    def test_that_email_address_is_required_when_none(self):
        self.assertRaises(
            ValidationError,
            OrganisationParent.objects.create,
            primary_ccg=create_test_ccg({}),
            choices_id=123
        )

    def test_that_email_address_is_required_when_empty(self):
        self.assertRaises(
            ValidationError,
            OrganisationParent.objects.create,
            primary_ccg=create_test_ccg({}),
            choices_id=123,
            email=""
        )


class CCGModelTests(TestCase):

    def setUp(self):
        # create a ccg
        self.test_ccg = create_test_ccg({'code': 'CCG1'})

        # create a trust
        self.test_trust = create_test_organisation_parent({'code': 'MYTRUST', 'primary_ccg': self.test_ccg})

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


class FriendsAndFamilySurveyModelTests(TransactionTestCase):

    fixtures = ['development_users.json']

    def setUp(self):
        super(FriendsAndFamilySurveyModelTests, self).setUp()


        # Below bits copied from AuthorizationTestCase because that's not a
        # TransactionTestCase and we need to be to test IntegrityErrors

        # CCGs
        self.test_ccg = create_test_ccg()
        self.other_test_ccg = create_test_ccg({'name': 'other test ccg', 'code': 'XYZ'})

        # Organisation Parent
        self.test_trust = create_test_organisation_parent({'primary_ccg': self.test_ccg})
        self.test_gp_surgery = create_test_organisation_parent({'name': 'other test trust',
                                                                'code': 'XYZ',
                                                                'primary_ccg': self.other_test_ccg})

        self.test_trust.ccgs.add(self.test_ccg)
        self.test_trust.save()
        self.test_gp_surgery.ccgs.add(self.other_test_ccg)
        self.test_gp_surgery.save()

        # Organisations
        self.test_hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                       'parent': self.test_trust,
                                                       'point': Point(-0.2, 51.5)})
        self.test_gp_branch = create_test_organisation({'ods_code': '12345',
                                                        'name': 'Test GP Branch',
                                                        'parent': self.test_gp_surgery,
                                                        'point': Point(-0.1, 51.5)})

        # Users
        self.test_password = 'password'

        # A Django superuser
        self.superuser = User.objects.get(pk=1)

        self.site_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_site.csv'
            )
        )

        self.trust_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_trust.csv'
            )
        )

    def login_as(self, user):
        logged_in = self.client.login(username=user.username, password=self.test_password)
        self.assertTrue(logged_in)

    def test_can_be_assigned_to_org_or_parent(self):

        organisation_type = ContentType.objects.get(
            app_label='organisations',
            model='organisation'
        )
        organisation_parent_type = ContentType.objects.get(
            app_label='organisations',
            model='organisationparent'
        )

        now = datetime.date.today()

        FriendsAndFamilySurvey.objects.create(
            content_object=self.test_hospital,
            location='ande',
            overall_score=75,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=now
        )

        FriendsAndFamilySurvey.objects.create(
            content_object=self.test_trust,
            overall_score=78,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=now
        )

        # These would error and fail the test if the things weren't in the DB
        FriendsAndFamilySurvey.objects.get(
            content_type=organisation_type,
            object_id=self.test_hospital.id
        )
        FriendsAndFamilySurvey.objects.get(
            content_type=organisation_parent_type,
            object_id=self.test_trust.id
        )

        self.assertEqual(self.test_hospital.surveys.all().count(), 1)

    def test_duplicate_site_surveys_not_allowed(self):
        now = datetime.date.today()

        survey = FriendsAndFamilySurvey(
            content_object=self.test_hospital,
            location='ande',
            overall_score=75,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=now
        )
        survey.save()

        with self.assertRaises(IntegrityError):
            survey = FriendsAndFamilySurvey(
                content_object=self.test_hospital,
                location='ande',
                overall_score=75,
                extremely_likely=10,
                likely=10,
                neither=1,
                unlikely=0,
                extremely_unlikely=1,
                dont_know=0,
                date=now
            )
            survey.save()

    def test_duplicate_trust_surveys_not_allowed(self):
        now = datetime.date.today()

        survey = FriendsAndFamilySurvey(
            content_object=self.test_trust,
            overall_score=78,
            extremely_likely=10,
            likely=10,
            neither=1,
            unlikely=0,
            extremely_unlikely=1,
            dont_know=0,
            date=now
        )
        survey.save()

        with self.assertRaises(IntegrityError):
            survey = FriendsAndFamilySurvey(
                content_object=self.test_trust,
                overall_score=78,
                extremely_likely=10,
                likely=10,
                neither=1,
                unlikely=0,
                extremely_unlikely=1,
                dont_know=0,
                date=now
            )
            survey.save()
            transaction.rollback()

    def test_process_csv_sites(self):
        today = datetime.date.today()

        created = FriendsAndFamilySurvey.process_csv(self.site_fixture_file, today, 'site', 'aande')

        self.assertEqual(len(created), 2)

        self.assertEqual(self.test_hospital.surveys.all().count(), 1)
        hospital_survey = self.test_hospital.surveys.all()[0]
        self.assertEqual(hospital_survey.date, today)
        self.assertEqual(hospital_survey.location, 'aande')
        self.assertEqual(hospital_survey.overall_score, 79)
        self.assertEqual(hospital_survey.extremely_likely, 346)
        self.assertEqual(hospital_survey.likely, 79)
        self.assertEqual(hospital_survey.neither, 6)
        self.assertEqual(hospital_survey.unlikely, 0)
        self.assertEqual(hospital_survey.extremely_unlikely, 0)
        self.assertEqual(hospital_survey.dont_know, 67)

        # Surveys won't normally be logged against GPs, but for the sake of
        # testing I added one in the fixture
        self.assertEqual(self.test_gp_branch.surveys.all().count(), 1)
        gp_survey = self.test_gp_branch.surveys.all()[0]
        self.assertEqual(gp_survey.date, today)
        self.assertEqual(gp_survey.location, 'aande')
        self.assertEqual(gp_survey.overall_score, 83)
        self.assertEqual(gp_survey.extremely_likely, 223)
        self.assertEqual(gp_survey.likely, 83)
        self.assertEqual(gp_survey.neither, 6)
        self.assertEqual(gp_survey.unlikely, 1)
        self.assertEqual(gp_survey.extremely_unlikely, 0)
        self.assertEqual(gp_survey.dont_know, 59)

    def test_process_csv_trusts(self):
        today = datetime.date.today()

        created = FriendsAndFamilySurvey.process_csv(self.trust_fixture_file, today, 'trust')

        self.assertEqual(len(created), 2)

        self.assertEqual(self.test_trust.surveys.all().count(), 1)
        trust_survey = self.test_trust.surveys.all()[0]
        self.assertEqual(trust_survey.location, '')
        self.assertEqual(trust_survey.date, today)
        self.assertEqual(trust_survey.overall_score, 79)
        self.assertEqual(trust_survey.extremely_likely, 346)
        self.assertEqual(trust_survey.likely, 79)
        self.assertEqual(trust_survey.neither, 6)
        self.assertEqual(trust_survey.unlikely, 0)
        self.assertEqual(trust_survey.extremely_unlikely, 0)
        self.assertEqual(trust_survey.dont_know, 67)

        # Surveys won't normally be logged against GPs, but for the sake of
        # testing I added one in the fixture
        self.assertEqual(self.test_gp_surgery.surveys.all().count(), 1)
        other_trust_survey = self.test_gp_surgery.surveys.all()[0]
        self.assertEqual(other_trust_survey.location, '')
        self.assertEqual(other_trust_survey.date, today)
        self.assertEqual(other_trust_survey.overall_score, 57)
        self.assertEqual(other_trust_survey.extremely_likely, 100)
        self.assertEqual(other_trust_survey.likely, 57)
        self.assertEqual(other_trust_survey.neither, 3)
        self.assertEqual(other_trust_survey.unlikely, 0)
        self.assertEqual(other_trust_survey.extremely_unlikely, 1)
        self.assertEqual(other_trust_survey.dont_know, 47)

    def test_missing_org_csv(self):
        today = datetime.date.today()

        missing_org_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_site.csv'
            )
        )

        with self.assertRaises(ValueError) as cm:
            FriendsAndFamilySurvey.process_csv(missing_org_fixture_file, today, 'site', 'aande')
            self.assertEqual(cm.exception.message, "Organisation with site code: NOTVALID (Test Organisation) is not in the database.")

    def test_missing_trust_csv(self):
        today = datetime.date.today()

        missing_trust_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_trust.csv'
            )
        )

        with self.assertRaises(ValueError) as cm:
            FriendsAndFamilySurvey.process_csv(missing_trust_fixture_file, today, 'trust')
            self.assertEqual(cm.exception.message, "OrganisationParent with code: NOTVALID (Test Trust) is not in the database.")

    def test_location_required_for_site_csvs(self):
        today = datetime.date.today()

        with self.assertRaises(ValueError) as cm:
            FriendsAndFamilySurvey.process_csv(self.site_fixture_file, today, 'site', location=None)
            self.assertEqual(cm.exception.message, "Location is required for site files.")

    def test_missing_fields_csv(self):
        today = datetime.date.today()

        missing_field_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_field.csv'
            )
        )

        with self.assertRaises(ValueError) as cm:
            FriendsAndFamilySurvey.process_csv(missing_field_fixture_file, today, 'site', 'aande')
            self.assertEqual(cm.exception.message, "Could not retrieve one of the score fields from the csv for: Test Organisation, or the data is not a valid score.")

    def test_bad_fields_csv(self):
        today = datetime.date.today()

        bad_field_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_bad_field.csv'
            )
        )

        with self.assertRaises(ValueError) as cm:
            FriendsAndFamilySurvey.process_csv(bad_field_fixture_file, today, 'site', 'aande')
            self.assertEqual(cm.exception.message, "Could not retrieve one of the score fields from the csv for: Test Organisation, or the data is not a valid score.")

    def test_duplicate_site_csv(self):
        today = datetime.date.today()

        # Put the csv through once, should work fine
        FriendsAndFamilySurvey.process_csv(self.site_fixture_file, today, 'site', 'aande')
        # Put it through again and we should get an IntegrityError
        with self.assertRaises(Exception) as cm:
            FriendsAndFamilySurvey.process_csv(self.site_fixture_file, today, 'site', 'aande')
            self.assertEqual(cm.exception.message, "There is already a survey for Test Organisation for the month January, 2013 and location A&E. Please delete the existing survey first if you're trying to replace it.")

    def test_duplicate_trust_csv(self):
        today = datetime.date.today()

        # Put the csv through once, should work fine
        FriendsAndFamilySurvey.process_csv(self.trust_fixture_file, today, 'trust')
        # Put it through again and we should get an IntegrityError
        with self.assertRaises(Exception) as cm:
            FriendsAndFamilySurvey.process_csv(self.trust_fixture_file, today, 'trust')
            self.assertEqual(cm.exception.message, "There is already a survey for Test Trust for the month January, 2013. Please delete the existing survey first if you're trying to replace it.")
