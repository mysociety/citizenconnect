import uuid

from django.test import TestCase

from organisations.tests import MockedChoicesAPITest

from ..models import Problem

class PublicViewTests(MockedChoicesAPITest):

    def setUp(self):
        super(PublicViewTests, self).setUp()
        self.uuid = uuid.uuid4().hex
        self.test_problem = Problem.objects.create(
            organisation_type='gppractices',
            choices_id=12702,
            description='This is a problem',
            category='cleanliness',
            reporter_name=self.uuid,
            reporter_email='steve@mysociety.org',
            reporter_phone='01111 111 111',
            public=True,
            public_reporter_name=True,
            preferred_contact_method='phone'
        )

    def test_public_problem_page_exists(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_problem_displays_organisation_name(self):
        resp = self.client.get("/choices/problem/{0}".format(self.test_problem.id))
        self.assertContains(resp, 'Test Organisation Name', count=1, status_code=200)
