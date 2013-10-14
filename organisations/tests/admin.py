# encoding: utf-8
from django.core.urlresolvers import reverse

from .lib import AuthorizationTestCase


class FriendsAndFamilySurveyFormTests(AuthorizationTestCase):

    def setUp(self):
        super(FriendsAndFamilySurveyFormTests, self).setUp()
        self.form_url = reverse("admin:organisations_friendsandfamilysurvey_survey_upload_csv")
        self.test_data = {
            'location': 'aande',
            'context': 'site',
            'month_month': 1,
            'month_year': 2013
        }

    def test_survey_csv_upload_page_exists(self):
        self.login_as(self.superuser)
        resp = self.client.get(self.form_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Upload Survey CSV")

    def test_survey_page_requires_all_fields(self):
        self.login_as(self.superuser)
        resp = self.client.post(self.form_url, {})
        self.assertFormError(resp, 'form', 'csv_file', 'This field is required.')
        self.assertFormError(resp, 'form', 'location', 'This field is required.')
        self.assertFormError(resp, 'form', 'context', 'This field is required.')
        self.assertFormError(resp, 'form', 'month', 'This field is required.')
