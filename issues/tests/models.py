from django.test import TestCase
from django.core.exceptions import ValidationError

from organisations.tests.lib import create_test_organisation, create_test_instance, AuthorizationTestCase

from ..models import Problem, Question

class ProblemModelTests(AuthorizationTestCase):

    def setUp(self):
        super(ProblemModelTests, self).setUp()
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
        self.test_moderated_problem = Problem(organisation=self.test_organisation,
                                    description='A Test Problem',
                                    category='cleanliness',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
                                    public=True,
                                    public_reporter_name=True,
                                    preferred_contact_method=Problem.CONTACT_EMAIL,
                                    status=Problem.NEW,
                                    moderated=Problem.MODERATED,
                                    publication_status=Problem.PUBLISHED)
        self.test_private_problem = Problem(organisation=self.test_organisation,
                                            description='A Test Private Problem',
                                            category='cleanliness',
                                            reporter_name='Test User',
                                            reporter_email='reporter@example.com',
                                            reporter_phone='01111 111 111',
                                            public=False,
                                            public_reporter_name=False,
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
        self.assertEqual(self.test_problem.publication_status, Problem.HIDDEN)

    def test_defaults_to_unmoderated(self):
        self.assertEqual(self.test_problem.moderated, Problem.NOT_MODERATED)

    def test_public_problem_accessible_to_everyone(self):
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.test_allowed_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.superuser))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.anonymous_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.test_other_provider_user))

    def test_private_problem_accessible_to_allowed_user(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.test_allowed_user))

    def test_private_problem_inaccessible_to_anon_user(self):
        self.assertFalse(self.test_private_problem.can_be_accessed_by(self.anonymous_user))

    def test_private_problem_inaccessible_to_other_provider_user(self):
        self.assertFalse(self.test_private_problem.can_be_accessed_by(self.test_other_provider_user))

    def test_private_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_private_problem.can_be_accessed_by(user))

    def test_private_problem_accessible_to_pals_user(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.test_pals_user))

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        self.assertFalse(self.test_problem.can_be_accessed_by(self.anonymous_user))

    def test_unmoderated_problem_inaccessible_to_other_provider_user(self):
        self.assertFalse(self.test_problem.can_be_accessed_by(self.test_other_provider_user))

    def test_unmoderated_problem_accessible_to_allowed_user(self):
        self.assertTrue(self.test_problem.can_be_accessed_by(self.test_allowed_user))

    def test_unmoderated_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_problem.can_be_accessed_by(user))

    def test_unmoderated_problem_accessible_to_pals_user(self):
        self.assertTrue(self.test_problem.can_be_accessed_by(self.test_pals_user))

class QuestionModelTests(TestCase):

    def setUp(self):
        self.test_question = Question(description='A Test Question',
                                    category='general',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
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

        # Problems that have been closed before being moderated
        self.closed_public_unmoderated_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'status':Problem.RESOLVED
        })
        self.closed_private_unmoderated_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'status':Problem.RESOLVED
        })

        # Problems that have been moderated
        self.new_public_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.HIDDEN
        })
        self.new_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.PUBLISHED
        })
        self.new_private_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.HIDDEN
        })
        self.new_private_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.PUBLISHED
        })

        # Problems that have been closed and moderated
        self.closed_public_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.HIDDEN,
            'status': Problem.RESOLVED
        })
        self.closed_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.PUBLISHED,
            'status': Problem.RESOLVED
        })
        self.closed_private_moderated_problem_hidden = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.HIDDEN,
            'status': Problem.RESOLVED
        })
        self.closed_private_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.PUBLISHED,
            'status': Problem.RESOLVED
        })

        self.open_unmoderated_problems = [self.new_public_unmoderated_problem,
                                          self.new_private_unmoderated_problem]

        self.closed_unmoderated_problems = [self.closed_public_unmoderated_problem,
                                             self.closed_private_unmoderated_problem]

        self.unmoderated_problems = self.open_unmoderated_problems + self.closed_unmoderated_problems

        self.open_moderated_problems = [self.new_public_moderated_problem_hidden,
                                         self.new_public_moderated_problem_published,
                                         self.new_private_moderated_problem_hidden,
                                         self.new_private_moderated_problem_published]

        self.open_problems = self.open_unmoderated_problems + self.open_moderated_problems

        self.open_moderated_published_problems = [self.new_public_moderated_problem_published,
                                        self.new_private_moderated_problem_published]

        self.closed_problems = self.closed_unmoderated_problems + [self.closed_public_moderated_problem_hidden,
                                                                    self.closed_public_moderated_problem_published,
                                                                    self.closed_private_moderated_problem_hidden,
                                                                    self.closed_private_moderated_problem_published]
        self.all_problems = self.open_problems + self.closed_problems

        self.all_moderated_published_public_problems = [self.new_public_moderated_problem_published, self.closed_public_moderated_problem_published]

    def test_open_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_problems(), self.open_problems)

    def test_unmoderated_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.unmoderated_problems(), self.unmoderated_problems)

    def test_open_moderated_published_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_moderated_published_problems(),
                               self.open_moderated_published_problems)

    def test_all_problems_returns_correct_questions(self):
        self.compare_querysets(Problem.objects.all(), self.all_problems)

    def test_all_moderated_published_public_problems_returns_correct_questions(self):
        self.compare_querysets(Problem.objects.all_moderated_published_public_problems(),
                               self.all_moderated_published_public_problems)

class QuestionManagerTests(ManagerTest):

    def setUp(self):
        self.open_question = create_test_instance(Question, {})
        self.closed_question = create_test_instance(Question, {
            'status': Question.RESOLVED
        })

        self.open_questions = [self.open_question]
        self.closed_questions = [self.closed_question]
        self.all_questions = self.open_questions + self.closed_questions

    def test_open_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.open_questions(), self.open_questions)

    def test_all_questions_returns_correct_questions(self):
        self.compare_querysets(Question.objects.all(), self.all_questions)
