from django.test import TestCase
from django.core.exceptions import ValidationError

from organisations.tests.lib import create_test_organisation

from ..models import Problem, Question

class ProblemModelTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_problem = Problem(organisation=self.test_organisation,
                                    description='A Test Problem',
                                    category='cleanliness',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
                                    public=True,
                                    public_reporter_name=True,
                                    preferred_contact_method=Problem.CONTACT_EMAIL,
                                    status=Problem.NEW)

    def test_has_prefix_property(self):
        self.assertEqual(Problem.PREFIX, 'P')
        self.assertEqual(self.test_problem.PREFIX, 'P')

    def test_has_reference_number_property(self):
        self.assertEqual(self.test_problem.reference_number, 'P{0}'.format(self.test_problem.id))

    def test_validates_phone_or_email_present(self):
        # Remove reporter email, should be fine as phone is set
        self.test_problem.reporter_email = None
        self.test_problem.clean()

        # Add email back in and remove phone, should also be fine
        self.test_problem.reporter_email = 'reporter@example.com'
        self.test_problem.reporter_phone = None
        self.test_problem.clean()

        # Remove both, it should error
        self.test_problem.reporter_phone = None
        self.test_problem.reporter_email = None
        with self.assertRaises(ValidationError) as context_manager:
            self.test_problem.clean()
        self.assertIsNotNone(context_manager.exception)

class QuestionModelTests(TestCase):

    def setUp(self):
        self.test_organisation = create_test_organisation()
        self.test_question = Question(organisation=self.test_organisation,
                                    description='A Test Question',
                                    category='general',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
                                    public=True,
                                    public_reporter_name=True,
                                    preferred_contact_method=Question.CONTACT_EMAIL,
                                    status=Question.NEW)

    def test_has_prefix_property(self):
        self.assertEqual(Question.PREFIX, 'Q')
        self.assertEqual(self.test_question.PREFIX, 'Q')

    def test_has_reference_number_property(self):
        self.assertEqual(self.test_question.reference_number, 'Q{0}'.format(self.test_question.id))

    def test_validates_phone_or_email_present(self):
        # Remove reporter email, should be fine as phone is set
        self.test_question.reporter_email = None
        self.test_question.clean()

        # Add email back in and remove phone, should also be fine
        self.test_question.reporter_email = 'reporter@example.com'
        self.test_question.reporter_phone = None
        self.test_question.clean()

        # Remove both, it should error
        self.test_question.reporter_phone = None
        self.test_question.reporter_email = None
        with self.assertRaises(ValidationError) as context_manager:
            self.test_question.clean()
        self.assertIsNotNone(context_manager.exception)
