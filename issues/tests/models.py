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
        # Set the preferred contact method to phone, else the validation will fail
        self.test_problem.preferred_contact_method = Problem.CONTACT_PHONE
        self.test_problem.clean()

        # Add email back in and remove phone, should also be fine
        self.test_problem.reporter_email = 'reporter@example.com'
        # Set the preferred contact method to email, else the validation will fail
        self.test_problem.preferred_contact_method = Problem.CONTACT_EMAIL
        self.test_problem.reporter_phone = None
        self.test_problem.clean()

        # Remove both, it should error
        self.test_problem.reporter_phone = None
        self.test_problem.reporter_email = None
        with self.assertRaises(ValidationError) as context_manager:
            self.test_problem.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide either a phone number or an email address')

    def test_validates_contact_method_given(self):
        # Remove email and set preferred contact method to email
        self.test_problem.reporter_email = None
        self.test_problem.preferred_contact_method = Problem.CONTACT_EMAIL

        with self.assertRaises(ValidationError) as context_manager:
            self.test_problem.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide an email address if you prefer to be contacted by email')

        # Remove phone and set preferred contact method to phone
        self.test_problem.reporter_email = 'reporter@example.com'
        self.test_problem.reporter_phone = None
        self.test_problem.preferred_contact_method = Problem.CONTACT_PHONE

        with self.assertRaises(ValidationError) as context_manager:
            self.test_problem.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide a phone number if you prefer to be contacted by phone')

    def test_defaults_to_not_mailed(self):
        self.assertFalse(self.test_problem.mailed)

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
        # Set the preferred contact method to phone, else the validation will fail
        self.test_question.preferred_contact_method = Question.CONTACT_PHONE
        self.test_question.clean()

        # Add email back in and remove phone, should also be fine
        self.test_question.reporter_email = 'reporter@example.com'
        # Set the preferred contact method to email, else the validation will fail
        self.test_question.preferred_contact_method = Question.CONTACT_EMAIL
        self.test_question.reporter_phone = None
        self.test_question.clean()

        # Remove both, it should error
        self.test_question.reporter_phone = None
        self.test_question.reporter_email = None
        with self.assertRaises(ValidationError) as context_manager:
            self.test_question.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide either a phone number or an email address')

    def test_validates_contact_method_given(self):
        # Remove email and set preferred contact method to email
        self.test_question.reporter_email = None
        self.test_question.preferred_contact_method = Problem.CONTACT_EMAIL

        with self.assertRaises(ValidationError) as context_manager:
            self.test_question.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide an email address if you prefer to be contacted by email')

        # Remove phone and set preferred contact method to phone
        self.test_question.reporter_email = 'reporter@example.com'
        self.test_question.reporter_phone = None
        self.test_question.preferred_contact_method = Problem.CONTACT_PHONE

        with self.assertRaises(ValidationError) as context_manager:
            self.test_question.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide a phone number if you prefer to be contacted by phone')

    def test_defaults_to_not_mailed(self):
        self.assertFalse(self.test_question.mailed)
