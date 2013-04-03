from datetime import datetime, timedelta
from random import randint
from mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.timezone import utc

from organisations.tests.lib import create_test_organisation, create_test_instance, AuthorizationTestCase

from ..models import Problem, Question
from ..lib import MistypedIDException

class ProblemTestCase(AuthorizationTestCase):

    def setUp(self):
        super(ProblemTestCase, self).setUp()
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
        self.test_hidden_status_problem = Problem(organisation=self.test_organisation,
                                                  description='A Test Hidden Problem',
                                                  category='cleanliness',
                                                  reporter_name='Test User',
                                                  reporter_email='reporter@example.com',
                                                  reporter_phone='01111 111 111',
                                                  public=True,
                                                  public_reporter_name=True,
                                                  preferred_contact_method=Problem.CONTACT_EMAIL,
                                                  status=Problem.ABUSIVE,
                                                  publication_status=Problem.PUBLISHED)

class ProblemModelTests(ProblemTestCase):

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
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.provider))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.superuser))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.anonymous_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.other_provider))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.other_ccg_user))

    def test_private_problem_accessible_to_allowed_user(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.provider))

    def test_private_problem_inaccessible_to_anon_user(self):
        self.assertFalse(self.test_private_problem.can_be_accessed_by(self.anonymous_user))

    def test_private_problem_inaccessible_to_other_provider_user(self):
        self.assertFalse(self.test_private_problem.can_be_accessed_by(self.other_provider))

    def test_private_problem_inaccessible_to_other_ccg_user(self):
        self.assertFalse(self.test_private_problem.can_be_accessed_by(self.other_ccg_user))

    def test_private_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_private_problem.can_be_accessed_by(user))

    def test_private_problem_accessible_to_pals_user(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.pals))

    def test_private_problem_accessible_to_ccg_user(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.ccg_user))

    def test_unmoderated_problem_inaccessible_to_anon_user(self):
        self.assertFalse(self.test_problem.can_be_accessed_by(self.anonymous_user))

    def test_unmoderated_problem_inaccessible_to_other_provider_user(self):
        self.assertFalse(self.test_problem.can_be_accessed_by(self.other_provider))

    def test_unmoderated_problem_inaccessible_to_other_ccg_user(self):
        self.assertFalse(self.test_problem.can_be_accessed_by(self.other_ccg_user))

    def test_unmoderated_problem_accessible_to_allowed_users(self):
        self.assertTrue(self.test_problem.can_be_accessed_by(self.provider))
        self.assertTrue(self.test_problem.can_be_accessed_by(self.ccg_user))

    def test_unmoderated_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_problem.can_be_accessed_by(user))

    def test_unmoderated_problem_accessible_to_pals_user(self):
        self.assertTrue(self.test_problem.can_be_accessed_by(self.pals))

    def test_hidden_status_problem_accessible_to_allowed_user(self):
        self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(self.provider))

    def test_hidden_status_problem_inaccessible_to_anon_user(self):
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.anonymous_user))

    def test_hidden_status_problem_inaccessible_to_other_provider_user(self):
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.other_provider))

    def test_hidden_status_problem_inaccessible_to_other_ccg_user(self):
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.other_ccg_user))

    def test_hidden_status_problem_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(user))

    def test_hidden_status_problem_accessible_to_pals_user(self):
        self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(self.pals))

    def test_hidden_status_problem_accessible_to_ccg_user(self):
        self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(self.ccg_user))

    def test_timedelta_to_minutes(self):
        t = timedelta(minutes=30)
        self.assertEqual(Problem.timedelta_to_minutes(t), 30)
        t = timedelta(hours=5)
        self.assertEqual(Problem.timedelta_to_minutes(t), 300)
        t = timedelta(days=5, hours=5, minutes=34, seconds=22)
        self.assertEqual(Problem.timedelta_to_minutes(t), 7534)

    def test_token_generated_returns_true_from_check(self):
        token = self.test_problem.make_token(24792)
        self.assertTrue(self.test_problem.check_token(token))

    def test_token_generated_with_different_hash_returns_false_from_check(self):
        token = self.test_problem.make_token(24792)
        rand, hash = token.split("-")
        different_token = "%s-%s" % (rand, "differenthash")
        self.assertFalse(self.test_problem.check_token(different_token))

    def test_mistyped_token_returns_false_from_check(self):
        token = self.test_problem.make_token(30464)
        self.assertEqual(token, 'xr0-bff54e08ca9de9f38b1f')
        self.assertFalse(self.test_problem.check_token('xro-bff54e08ca9de9f38b1f'))

class ProblemModelTimeToTests(ProblemTestCase):

    def setUp(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        super(ProblemModelTimeToTests, self).setUp()
        self.test_problem.created = now - timedelta(days=5)

    def test_sets_time_to_ack_when_saved_in_ack_status_and_time_to_ack_not_set(self):
        self.test_problem.status = Problem.ACKNOWLEDGED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, 7200)

    def test_does_not_set_time_to_ack_when_saved_in_ack_status_and_time_to_ack_set(self):
        self.test_problem.time_to_acknowledge = 2000
        self.test_problem.status = Problem.ACKNOWLEDGED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, 2000)

    def test_does_not_set_time_to_ack_when_saved_in_new_status_and_time_to_ack_not_set(self):
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, None)

    def test_does_not_set_time_to_ack_when_saved_in_escalated_status_and_time_to_ack_not_set(self):
        self.test_problem.status = Problem.ESCALATED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, None)

    def test_sets_time_to_ack_when_saved_in_resolved_status_and_time_to_ack_not_set(self):
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, 7200)

    def test_sets_time_to_address_when_saved_in_resolved_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, 7200)

    def test_does_not_set_time_to_address_when_saved_in_resolved_status_and_time_to_address_set(self):
        self.test_problem.time_to_address = 3000
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, 3000)

    def test_does_not_set_time_to_address_when_saved_in_new_status_and_time_to_address_not_set(self):
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, None)

    def test_does_not_set_time_to_address_when_saved_in_ack_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.ACKNOWLEDGED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, None)

    def test_does_not_set_time_to_address_when_saved_in_escalated_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.ESCALATED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, None)


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

        # Problems that have been escalated and moderated
        self.escalated_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'publication_status':Problem.PUBLISHED,
            'status': Problem.ESCALATED
        })

        # Unmoderated escalated problems
        self.escalated_private_unmoderated_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'status': Problem.ESCALATED
        })

        # A breach of care standards problem
        self.breach_public_moderated_problem_published = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public': True,
            'status': Problem.ACKNOWLEDGED,
            'breach': True,
            'moderated': Problem.MODERATED,
            'publication_status': Problem.PUBLISHED
        })

        # Problems requiring second tier moderation
        self.public_problem_requiring_second_tier_moderation = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':True,
            'moderated':Problem.MODERATED,
            'requires_second_tier_moderation': True,
            'publication_status': Problem.HIDDEN
        })
        self.private_problem_requiring_second_tier_moderation = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public':False,
            'moderated':Problem.MODERATED,
            'requires_second_tier_moderation': True,
            'publication_status': Problem.HIDDEN
        })

        # Problems in hidden statuses
        self.public_published_unresolvable_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public': True,
            'moderated': Problem.MODERATED,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.UNABLE_TO_RESOLVE
        })

        self.public_published_abusive_problem = create_test_instance(Problem, {
            'organisation': self.test_organisation,
            'public': True,
            'moderated': Problem.MODERATED,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.ABUSIVE
        })



        # Intermediate helper lists
        self.open_unmoderated_problems = [self.new_public_unmoderated_problem,
                                          self.new_private_unmoderated_problem,
                                          self.escalated_private_unmoderated_problem]
        self.closed_unmoderated_problems = [self.closed_public_unmoderated_problem,
                                            self.closed_private_unmoderated_problem]
        self.open_moderated_problems = [self.new_public_moderated_problem_hidden,
                                        self.new_public_moderated_problem_published,
                                        self.new_private_moderated_problem_hidden,
                                        self.new_private_moderated_problem_published,
                                        self.escalated_public_moderated_problem_published,
                                        self.public_problem_requiring_second_tier_moderation,
                                        self.private_problem_requiring_second_tier_moderation,
                                        self.breach_public_moderated_problem_published]
        self.closed_problems = self.closed_unmoderated_problems + [self.closed_public_moderated_problem_hidden,
                                                                   self.closed_public_moderated_problem_published,
                                                                   self.closed_private_moderated_problem_hidden,
                                                                   self.closed_private_moderated_problem_published,
                                                                   self.public_published_unresolvable_problem,
                                                                   self.public_published_abusive_problem]

        # Lists that we expect from our manager's methods
        self.unmoderated_problems = self.open_unmoderated_problems + self.closed_unmoderated_problems
        self.open_problems = self.open_unmoderated_problems + self.open_moderated_problems
        self.open_moderated_published_problems = [self.new_public_moderated_problem_published,
                                                  self.new_private_moderated_problem_published,
                                                  self.escalated_public_moderated_problem_published,
                                                  self.breach_public_moderated_problem_published]
        self.all_problems = self.open_problems + self.closed_problems
        self.all_moderated_published_problems = self.open_moderated_published_problems + [self.closed_public_moderated_problem_published,
                                                                                          self.closed_private_moderated_problem_published]
        self.problems_requiring_second_tier_moderation = [self.public_problem_requiring_second_tier_moderation,
                                                    self.private_problem_requiring_second_tier_moderation]

        self.open_escalated_problems = [self.breach_public_moderated_problem_published,
                                        self.escalated_public_moderated_problem_published,
                                        self.escalated_private_unmoderated_problem]

    def test_all_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all(), self.all_problems)

    def test_open_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_problems(), self.open_problems)

    def test_unmoderated_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.unmoderated_problems(), self.unmoderated_problems)

    def test_open_moderated_published_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_moderated_published_problems(),
                               self.open_moderated_published_problems)

    def test_all_moderated_published_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all_moderated_published_problems(),
                               self.all_moderated_published_problems)

    def test_problems_requiring_second_tier_moderation_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.problems_requiring_second_tier_moderation(),
                               self.problems_requiring_second_tier_moderation)

    def test_escalated_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_escalated_problems(),
                               self.open_escalated_problems)

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
