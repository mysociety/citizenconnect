# encoding: utf-8
import os
import datetime

from django.core.urlresolvers import reverse
from django.db import IntegrityError

from .lib import AuthorizationTestCase


class FriendsAndFamilySurveyFormTests(AuthorizationTestCase):

    def setUp(self):
        super(FriendsAndFamilySurveyFormTests, self).setUp()
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
            'context': 'trust',
            'month_month': 1,
            'month_year': 2013
        }

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

    def test_location_required_for_site_files(self):
        self.login_as(self.superuser)
        test_data = self.site_test_data.copy()
        del test_data['location']
        resp = self.client.post(self.form_url, test_data)
        self.assertFormError(resp, 'form', 'location', 'Location is required for Site files.')

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
        self.assertEqual(trust_survey.location, '')
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
        self.assertEqual(other_trust_survey.location, '')
        self.assertEqual(other_trust_survey.date, expected_date)
        self.assertEqual(other_trust_survey.overall_score, 57)
        self.assertEqual(other_trust_survey.extremely_likely, 100)
        self.assertEqual(other_trust_survey.likely, 57)
        self.assertEqual(other_trust_survey.neither, 3)
        self.assertEqual(other_trust_survey.unlikely, 0)
        self.assertEqual(other_trust_survey.extremely_unlikely, 1)
        self.assertEqual(other_trust_survey.dont_know, 47)
