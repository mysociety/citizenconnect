import uuid

from django.test import TestCase

from organisations.tests import MockedChoicesAPITest

from ..models import Question

class PublicViewTests(MockedChoicesAPITest):

    def setUp(self):
        super(PublicViewTests, self).setUp()
        self.uuid = uuid.uuid4().hex
        self.test_question = Question.objects.create(
            organisation_type='gppractices',
            choices_id=12702,
            description='This is a question',
            category='services',
            reporter_name=self.uuid,
            reporter_email='steve@mysociety.org',
            reporter_phone='01111 111 111',
            public=True,
            public_reporter_name=True,
            preferred_contact_method='phone'
        )

    def test_public_question_page_exists(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertEqual(resp.status_code, 200)

    def test_public_question_displays_organisation_name(self):
        resp = self.client.get("/choices/question/{0}".format(self.test_question.id))
        self.assertContains(resp, 'Test Organisation Name', count=1, status_code=200)
