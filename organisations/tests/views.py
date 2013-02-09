from . import MockedChoicesAPITest

class OrganisationSummaryTests(MockedChoicesAPITest):

    def setUp(self):
        super(OrganisationSummaryTests, self).setUp()
        self.summary_url = '/choices/stats/summary/gppractices/12702'

    def test_summary_page_exists(self):
        resp = self.client.get(self.summary_url)
        self.assertEqual(resp.status_code, 200)

    def test_summary_page_shows_organisation_name(self):
        resp = self.client.get(self.summary_url)
        self.assertTrue('Test Organisation Name Outcomes' in resp.content)

