# encoding: utf-8
import os
import datetime

from django.test import TransactionTestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.gis.geos import Point

from .lib import (
    create_test_organisation,
    create_test_ccg,
    create_test_organisation_parent
)

from ..models import FriendsAndFamilySurvey


class FriendsAndFamilySurveyFormTests(TransactionTestCase):

    fixtures = ['development_users.json']

    def setUp(self):
        super(FriendsAndFamilySurveyFormTests, self).setUp()


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

        self.form_url = reverse("admin:organisations_friendsandfamilysurvey_survey_upload_csv")
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
        self.site_test_data = {
            'csv_file': self.site_fixture_file,
            'location': 'aande',
            'context': 'site',
            'month_month': 1,
            'month_year': 2013
        }
        self.trust_test_data = {
            'csv_file': self.trust_fixture_file,
            'location': 'aande',
            'context': 'trust',
            'month_month': 1,
            'month_year': 2013
        }

    def login_as(self, user):
        logged_in = self.client.login(username=user.username, password=self.test_password)
        self.assertTrue(logged_in)

    def test_survey_csv_upload_page_exists(self):
        self.login_as(self.superuser)
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Upload Survey CSV")

    def test_survey_page_required_fields(self):
        self.login_as(self.superuser)
        resp = self.client.post(self.form_url, {})
        self.assertFormError(resp, 'form', 'csv_file', 'This field is required.')
        self.assertFormError(resp, 'form', 'context', 'This field is required.')
        self.assertFormError(resp, 'form', 'month', 'This field is required.')
        self.assertFormError(resp, 'form', 'location', 'This field is required.')

    def test_happy_path_sites(self):
        self.login_as(self.superuser)
        self.client.post(self.form_url, self.site_test_data)

        expected_date = datetime.date(2013, 1, 1)

        self.assertEqual(self.test_hospital.surveys.all().count(), 1)
        hospital_survey = self.test_hospital.surveys.all()[0]
        self.assertEqual(hospital_survey.date, expected_date)
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
        self.assertEqual(gp_survey.date, expected_date)
        self.assertEqual(gp_survey.location, 'aande')
        self.assertEqual(gp_survey.overall_score, 83)
        self.assertEqual(gp_survey.extremely_likely, 223)
        self.assertEqual(gp_survey.likely, 83)
        self.assertEqual(gp_survey.neither, 6)
        self.assertEqual(gp_survey.unlikely, 1)
        self.assertEqual(gp_survey.extremely_unlikely, 0)
        self.assertEqual(gp_survey.dont_know, 59)

    def test_happy_path_trusts(self):
        self.login_as(self.superuser)
        self.client.post(self.form_url, self.trust_test_data)

        expected_date = datetime.date(2013, 1, 1)

        self.assertEqual(self.test_trust.surveys.all().count(), 1)
        trust_survey = self.test_trust.surveys.all()[0]
        self.assertEqual(trust_survey.location, 'aande')
        self.assertEqual(trust_survey.date, expected_date)
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
        self.assertEqual(other_trust_survey.location, 'aande')
        self.assertEqual(other_trust_survey.date, expected_date)
        self.assertEqual(other_trust_survey.overall_score, 57)
        self.assertEqual(other_trust_survey.extremely_likely, 100)
        self.assertEqual(other_trust_survey.likely, 57)
        self.assertEqual(other_trust_survey.neither, 3)
        self.assertEqual(other_trust_survey.unlikely, 0)
        self.assertEqual(other_trust_survey.extremely_unlikely, 1)
        self.assertEqual(other_trust_survey.dont_know, 47)

    def test_missing_fields(self):
        self.login_as(self.superuser)
        test_data = self.site_test_data.copy()
        missing_field_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_field.csv'
            )
        )
        test_data['csv_file'] = missing_field_fixture_file
        resp = self.client.post(self.form_url, test_data)
        self.assertContains(resp, "Could not retrieve one of the score fields from the csv for: Test Organisation, or the data is not a valid score.")
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 0)

    def test_bad_fields(self):
        self.login_as(self.superuser)
        test_data = self.site_test_data.copy()
        bad_field_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_bad_field.csv'
            )
        )
        test_data['csv_file'] = bad_field_fixture_file
        resp = self.client.post(self.form_url, test_data)
        self.assertContains(resp, "Could not retrieve one of the score fields from the csv for: Test Organisation, or the data is not a valid score.")
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 0)

    def test_missing_org(self):
        self.login_as(self.superuser)
        test_data = self.site_test_data.copy()
        missing_org_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_site.csv'
            )
        )
        test_data['csv_file'] = missing_org_fixture_file
        self.client.post(self.form_url, test_data)
        # Should skip the bad orgs and just save the good ones
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 1)

    def test_missing_trust(self):
        self.login_as(self.superuser)
        test_data = self.trust_test_data.copy()
        missing_trust_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_missing_trust.csv'
            )
        )
        test_data['csv_file'] = missing_trust_fixture_file
        self.client.post(self.form_url, test_data)
        # Should skip the bad trusts and just save the good ones
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 1)

    def test_duplicate_org_survey(self):
        self.login_as(self.superuser)

        self.client.post(self.form_url, self.site_test_data)
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 2)

        # Posting the test data blanks some stuff from it, so we send a copy
        # the second time
        site_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_site.csv'
            )
        )
        site_test_data = {
            'csv_file': site_fixture_file,
            'location': 'aande',
            'context': 'site',
            'month_month': 1,
            'month_year': 2013
        }

        resp = self.client.post(self.form_url, site_test_data)
        self.assertContains(resp, "There is already a survey for Test Organisation for the month January, 2013 and location A&amp;E. Please delete the existing survey first if you&#39;re trying to replace it.")
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 2)

    def test_duplicate_trust_survey(self):
        self.login_as(self.superuser)

        self.client.post(self.form_url, self.trust_test_data)
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 2)

        # Posting the test data blanks some stuff from it, so we send a copy
        # the second time
        trust_fixture_file = open(
            os.path.join(
                os.path.dirname(__file__),
                'fixtures',
                'fft_survey_trust.csv'
            )
        )
        trust_test_data = {
            'csv_file': trust_fixture_file,
            'location': 'aande',
            'context': 'trust',
            'month_month': 1,
            'month_year': 2013
        }

        resp = self.client.post(self.form_url, trust_test_data)
        self.assertContains(resp, "There is already a survey for Test Trust for the month January, 2013 and location A&amp;E. Please delete the existing survey first if you&#39;re trying to replace it.")
        self.assertEqual(FriendsAndFamilySurvey.objects.all().count(), 2)

