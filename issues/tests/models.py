from django.test import TestCase
from django.core.exceptions import ValidationError

from organisations.tests.lib import create_test_organisation, create_test_instance

from ..models import Problem, Question, MessageModel

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

    def test_defaults_to_hidden(self):
        self.assertEqual(self.test_problem.publication_status, MessageModel.HIDDEN)

    def test_defaults_to_unmoderated(self):
        self.assertEqual(self.test_problem.moderated, MessageModel.NOT_MODERATED)


class QuestionModelTests(TestCase):

    def setUp(self):
        self.test_question = Question(description='A Test Question',
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

    def test_defaults_to_hidden(self):
        self.assertEqual(self.test_question.publication_status, MessageModel.HIDDEN)

    def test_defaults_to_unmoderated(self):
        self.assertEqual(self.test_question.moderated, MessageModel.NOT_MODERATED)

class ManagerTest(TestCase):

    def compare_querysets(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for model in expected:
            self.assertTrue(model in actual)

class ProblemManagerTests(ManagerTest):

    def setUp(self):
        self.test_organisation = create_test_organisation()

        # Brand new problems
        self.new_public_unmoderated_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True
        })
        self.new_private_unmoderated_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False
        })

        # Problems that have been moderated
        self.new_public_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN
        })
        self.new_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED
        })
        self.new_private_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN
        })
        self.new_private_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED
        })

        # Problems that have been closed
        self.closed_public_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN,
            'status': Problem.RESOLVED
        })
        self.closed_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED,
            'status': Problem.RESOLVED
        })
        self.closed_private_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN,
            'status': Problem.RESOLVED
        })
        self.closed_private_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED,
            'status': Problem.RESOLVED
        })

        self.open_unmoderated_problems = [self.new_public_unmoderated_problem, self.new_public_unmoderated_problem]
        self.open_moderated_problems = [self.new_public_moderated_problem_hidden,
                                         self.new_public_moderated_problem_published,
                                         self.new_private_moderated_problem_hidden,
                                         self.new_private_moderated_problem_published]
        self.open_problems = self.open_unmoderated_problems + self.open_moderated_problems
        self.open_moderated_published_problems = [self.new_public_moderated_problem_published,
                                        self.new_private_moderated_problem_published]
        self.open_moderated_published_public_problems = [self.new_public_moderated_problem_published]
        self.closed_problems = [self.closed_public_moderated_problem_hidden,
                                self.closed_public_moderated_problem_published,
                                self.closed_private_moderated_problem_hidden,
                                self.closed_private_moderated_problem_published]

        self.all_problems = self.open_problems + self.closed_problems

    def test_open_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_problems(), self.open_problems)

    def test_open_moderated_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_moderated_problems(), self.open_moderated_problems)

    def test_open_unmoderated_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_unmoderated_problems(), self.open_unmoderated_problems)

    def test_open_moderated_published_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_moderated_published_problems(),
                               self.open_moderated_published_problems)

    def test_open_moderated_published_public_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_moderated_published_public_problems(),
                               self.open_moderated_published_public_problems)

    def test_all_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all(), self.all_problems)

class QuestionManagerTests(ManagerTest):

    def setUp(self):
        # Brand new questions
        self.new_public_unmoderated_question = create_test_instance(Question, {
            'public':True
        })
        self.new_private_unmoderated_question = create_test_instance(Question, {
            'public':False
        })

        # Questions that have been moderated
        self.new_public_moderated_question_hidden = create_test_instance(Question, {
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN
        })
        self.new_public_moderated_question_published = create_test_instance(Question, {
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED
        })
        self.new_private_moderated_question_hidden = create_test_instance(Question, {
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN
        })
        self.new_private_moderated_question_published = create_test_instance(Question, {
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED
        })

        # Questions that have been closed
        self.closed_public_moderated_question_hidden = create_test_instance(Question, {
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN,
            'status': Question.RESOLVED
        })
        self.closed_public_moderated_question_published = create_test_instance(Question, {
            'public':True,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED,
            'status': Question.RESOLVED
        })
        self.closed_private_moderated_question_hidden = create_test_instance(Question, {
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.HIDDEN,
            'status': Question.RESOLVED
        })
        self.closed_private_moderated_question_published = create_test_instance(Question, {
            'public':False,
            'moderated':MessageModel.MODERATED,
            'publication_status':MessageModel.PUBLISHED,
            'status': Question.RESOLVED
        })

        self.open_unmoderated_questions = [self.new_public_unmoderated_question, self.new_public_unmoderated_question]
        self.open_moderated_questions = [self.new_public_moderated_question_hidden,
                                         self.new_public_moderated_question_published,
                                         self.new_private_moderated_question_hidden,
                                         self.new_private_moderated_question_published]
        self.open_questions = self.open_unmoderated_questions + self.open_moderated_questions
        self.open_moderated_published_questions = [self.new_public_moderated_question_published,
                                        self.new_private_moderated_question_published]
        self.open_moderated_published_public_questions = [self.new_public_moderated_question_published]
        self.closed_questions = [self.closed_public_moderated_question_hidden,
                                self.closed_public_moderated_question_published,
                                self.closed_private_moderated_question_hidden,
                                self.closed_private_moderated_question_published]

        self.all_questions = self.open_questions + self.closed_questions

    def test_open_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_questions(), self.open_questions)

    def test_open_moderated_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_moderated_questions(), self.open_moderated_questions)

    def test_open_unmoderated_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_unmoderated_questions(), self.open_unmoderated_questions)

    def test_open_moderated_published_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_moderated_published_questions(),
                               self.open_moderated_published_questions)

    def test_open_moderated_published_public_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_moderated_published_public_questions(),
                               self.open_moderated_published_public_questions)

    def test_all_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.all(), self.all_questions)
