import warnings
import re
from datetime import datetime, timedelta
from time import strftime, gmtime
from mock import patch

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.conf import settings
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.files.images import ImageFile
from django.utils.timezone import utc

from concurrency.utils import ConcurrencyTestMixin

from organisations.tests.lib import create_test_organisation, create_test_problem, AuthorizationTestCase

from ..models import Problem, ProblemImage

from .lib import ProblemImageTestBase


class ProblemTestCase(AuthorizationTestCase):

    def setUp(self):
        super(ProblemTestCase, self).setUp()

        # A brand new, unmoderated problem, all public
        self.test_problem = Problem(organisation=self.test_hospital,
                                    description='A Test Problem',
                                    category='cleanliness',
                                    reporter_name='Test User',
                                    reporter_email='reporter@example.com',
                                    reporter_phone='01111 111 111',
                                    public=True,
                                    public_reporter_name=True,
                                    preferred_contact_method=Problem.CONTACT_EMAIL,
                                    status=Problem.NEW,
                                    time_to_acknowledge=None,
                                    time_to_address=None)

        # A brand new, moderated problem, all public
        self.test_moderated_problem = Problem(organisation=self.test_hospital,
                                              description='A Test Problem',
                                              moderated_description='A Test Problem (moderated)',
                                              category='cleanliness',
                                              reporter_name='Test User',
                                              reporter_email='reporter@example.com',
                                              reporter_phone='01111 111 111',
                                              public=True,
                                              public_reporter_name=True,
                                              preferred_contact_method=Problem.CONTACT_EMAIL,
                                              status=Problem.NEW,
                                              publication_status=Problem.PUBLISHED,
                                              time_to_acknowledge=None,
                                              time_to_address=None,
                                              cobrand='choices')

        # A brand new, unmoderated problem that the user would like kept private
        self.test_private_problem = Problem(organisation=self.test_hospital,
                                            description='A Test Private Problem',
                                            category='cleanliness',
                                            reporter_name='Test User',
                                            reporter_email='reporter@example.com',
                                            reporter_phone='01111 111 111',
                                            public=False,
                                            public_reporter_name=False,
                                            preferred_contact_method=Problem.CONTACT_EMAIL,
                                            status=Problem.NEW,
                                            time_to_acknowledge=None,
                                            time_to_address=None,
                                            cobrand='choices')

        # A problem that has been moderated and rejected - ie: not published
        self.test_moderated_hidden_problem = Problem(
            organisation=self.test_hospital,
            description='A Test Private Problem',
            category='cleanliness',
            reporter_name='Test User',
            reporter_email='reporter@example.com',
            reporter_phone='01111 111 111',
            public=True,
            public_reporter_name=True,
            preferred_contact_method=Problem.CONTACT_EMAIL,
            status=Problem.NEW,
            publication_status=Problem.REJECTED,
            time_to_acknowledge=None,
            time_to_address=None,
            cobrand='choices'
        )

        # A problem that has been moderated, and marked as Abusive/Vexatious
        # (hence should not be shown to the public) but passed moderation.
        # (Not sure how that would happen in real life, perhaps a spam repeat
        # of a similar one)
        self.test_hidden_status_problem = Problem(organisation=self.test_hospital,
                                                  description='A Test Rejected Problem',
                                                  category='cleanliness',
                                                  reporter_name='Test User',
                                                  reporter_email='reporter@example.com',
                                                  reporter_phone='01111 111 111',
                                                  public=True,
                                                  public_reporter_name=True,
                                                  preferred_contact_method=Problem.CONTACT_EMAIL,
                                                  status=Problem.ABUSIVE,
                                                  publication_status=Problem.PUBLISHED,
                                                  time_to_acknowledge=None,
                                                  time_to_address=None,
                                                  cobrand='choices')


class ProblemModelTests(ProblemTestCase):

    def test_get_absolute_url(self):
        self.test_problem.save()
        problem_url = reverse('problem-view', kwargs={'pk': self.test_problem.id, 'cobrand': 'choices'})
        self.assertEqual(
            self.test_problem.get_absolute_url(),
            problem_url
        )

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

    def test_validates_phone_number_if_phone_preferred(self):
        # Remove phone and set preferred contact method to phone
        self.test_problem.reporter_email = 'reporter@example.com'
        self.test_problem.reporter_phone = None
        self.test_problem.preferred_contact_method = Problem.CONTACT_PHONE

        with self.assertRaises(ValidationError) as context_manager:
            # We're only testing our clean() method here, so just call that
            self.test_problem.clean()

        self.assertEqual(context_manager.exception.messages[0], 'You must provide a phone number if you prefer to be contacted by phone')

    def test_defaults_to_not_mailed(self):
        self.assertFalse(self.test_problem.mailed)

    def test_defaults_to_not_under_16(self):
        self.assertFalse(self.test_problem.reporter_under_16)

    def test_under_16s_name_never_public(self):
        problem = self.test_problem
        problem.reporter_under_16 = True
        problem.public_reporter_name = True

        # Should not pass clean
        with self.assertRaises(ValidationError) as context_manager:
            problem.full_clean()
        self.assertEqual(context_manager.exception.messages[0], 'The reporter name cannot public if the reporter is under 16.')

        # This should be is ok (ie not raise exception)
        problem.public_reporter_name = False
        problem.full_clean()

    def test_public_reporter_name_original(self):
        # test set to the same as public_reporter_name when creating
        public_name_problem = create_test_problem({ "public_reporter_name": True, 'organisation': self.test_hospital })
        self.assertTrue( public_name_problem.public_reporter_name_original )
        private_name_problem = create_test_problem({ "public_reporter_name": False, 'organisation': self.test_hospital })
        self.assertFalse( private_name_problem.public_reporter_name_original )

        # test public_reporter_name_original cannot be changed
        with self.assertRaises(Exception):
            private_name_problem.public_reporter_name_original = True
            private_name_problem.save()

        # test that public_reporter_name cannot be true if public_reporter_name_original is false
        private_name_problem = Problem.objects.get(pk=private_name_problem.pk)
        with self.assertRaises(Exception):
            private_name_problem.public_reporter_name = True
            private_name_problem.save()

    def test_public_false_means_public_reporter_name_false_too(self):

        problem = create_test_problem({
            "public": False,
            "public_reporter_name": True,
            "organisation": self.test_hospital,
        })

        self.assertFalse( problem.public )
        self.assertFalse( problem.public_reporter_name )
        self.assertFalse( problem.public_reporter_name_original )

    def test_defaults_to_no_confirmation_sent(self):
        self.assertFalse(self.test_problem.confirmation_sent)

    def test_defaults_to_confirmation_not_required(self):
        self.assertFalse(self.test_problem.confirmation_required)

    def test_defaults_to_not_moderated(self):
        self.assertEqual(self.test_problem.publication_status, Problem.NOT_MODERATED)

    def test_moderated_public_problem_accessible_to_everyone(self):
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.anonymous_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.gp_surgery_user))
        self.assertTrue(self.test_moderated_problem.can_be_accessed_by(self.other_ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_moderated_problem.can_be_accessed_by(user))

    def test_unmoderated_public_problem_accessible_to_everyone(self):
        self.assertTrue(self.test_problem.can_be_accessed_by(self.anonymous_user))
        self.assertTrue(self.test_problem.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_problem.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.test_problem.can_be_accessed_by(self.gp_surgery_user))
        self.assertTrue(self.test_problem.can_be_accessed_by(self.other_ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_problem.can_be_accessed_by(user))

    def test_unmoderated_private_problem_accessible_to_everyone(self):
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.anonymous_user))
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.ccg_user))
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.gp_surgery_user))
        self.assertTrue(self.test_private_problem.can_be_accessed_by(self.other_ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_private_problem.can_be_accessed_by(user))

    def test_moderated_hidden_problem_accessible_to_allowed_users(self):
        self.assertTrue(self.test_moderated_hidden_problem.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_moderated_hidden_problem.can_be_accessed_by(self.ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_moderated_hidden_problem.can_be_accessed_by(user))

    def test_moderated_hidden_problem_inaccessible_to_not_allowed_users(self):
        self.assertFalse(self.test_moderated_hidden_problem.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.test_moderated_hidden_problem.can_be_accessed_by(self.gp_surgery_user))
        self.assertFalse(self.test_moderated_hidden_problem.can_be_accessed_by(self.other_ccg_user))

    def test_hidden_status_problem_accessible_to_allowed_users(self):
        self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(self.trust_user))
        self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(self.ccg_user))
        for user in self.users_who_can_access_everything:
            self.assertTrue(self.test_hidden_status_problem.can_be_accessed_by(user))

    def test_hidden_status_problem_inaccessible_to_not_allowed_users(self):
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.anonymous_user))
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.gp_surgery_user))
        self.assertFalse(self.test_hidden_status_problem.can_be_accessed_by(self.other_ccg_user))

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
        with self.settings(SECRET_KEY="value needs to be consistent to ensure same token created"):
            token = self.test_problem.make_token(30464)
            self.assertEqual(token, 'xr0-0ca2b7902598992daf25')
            self.assertTrue(self.test_problem.check_token(token))
            self.assertFalse(self.test_problem.check_token('xro-0ca2b7902598992daf25'))

    def test_has_elevated_priority(self):
        problem = self.test_problem
        self.assertEqual(problem.priority, Problem.PRIORITY_NORMAL)
        self.assertEqual(problem.has_elevated_priority, False)
        problem.priority = Problem.PRIORITY_HIGH
        self.assertEqual(problem.priority, Problem.PRIORITY_HIGH)
        self.assertEqual(problem.has_elevated_priority, True)

    def test_is_high_priority(self):
        problem = self.test_problem
        self.assertFalse(problem.is_high_priority)
        problem.priority = Problem.PRIORITY_HIGH
        self.assertTrue(problem.is_high_priority)
        problem.status = Problem.RESOLVED
        self.assertFalse(problem.is_high_priority)

    def test_limits_description_to_2000_chars(self):
        long_problem = self.test_problem
        long_problem.description = "a" * 2001

        with self.assertRaises(ValidationError) as context_manager:
            long_problem.full_clean()
        self.assertEqual(len(context_manager.exception.messages), 1)
        self.assertEqual(context_manager.exception.messages[0], 'Ensure this value has at most 2000 characters (it has 2001).')

    def test_formal_complaint_defaults_to_false(self):
        self.assertEqual(self.test_problem.formal_complaint, False)

    def test_defaults_to_primary_cobrand(self):
        self.assertEqual(self.test_problem.cobrand, 'choices')

    def test_summary(self):
        tests = (
            # (problem, expected summary)
            (self.test_problem, "Awaiting moderation"),
            (self.test_moderated_problem, "A Test Problem (moderated)"),
            (self.test_moderated_hidden_problem, "Hidden"),
            (self.test_private_problem, "Private"),
        )

        for problem, expected_summary in tests:
            self.assertEqual(problem.summary, expected_summary)


class ProblemModelTimeToTests(ProblemTestCase):

    def setUp(self):
        self.now = datetime.utcnow().replace(tzinfo=utc)
        super(ProblemModelTimeToTests, self).setUp()
        self.test_problem.created = self.now - timedelta(days=5)

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
        self.test_problem.commissioned = Problem.LOCALLY_COMMISSIONED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, None)

    def test_sets_time_to_ack_when_saved_in_resolved_status_and_time_to_ack_not_set(self):
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, 7200)

    def test_sets_time_to_ack_when_saved_in_escalated_ack_status_and_time_to_ack_not_set(self):
        self.test_problem.status = Problem.ESCALATED_ACKNOWLEDGED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_acknowledge, 7200)

    def test_sets_time_to_address_when_saved_in_resolved_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, 7200)

    def test_sets_time_to_address_when_saved_in_escalated_resolved_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.ESCALATED_RESOLVED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, 7200)

    def test_sets_resolved_when_saved_in_resolved_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.RESOLVED
        self.test_problem.save()
        self.assertAlmostEqual(self.test_problem.resolved, self.now, delta=timedelta(seconds=10))

    def test_sets_resolved_when_saved_in_escalated_resolved_status_and_time_to_address_not_set(self):
        self.test_problem.status = Problem.ESCALATED_RESOLVED
        self.test_problem.save()
        self.assertAlmostEqual(self.test_problem.resolved, self.now, delta=timedelta(seconds=10))

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
        self.test_problem.commissioned = Problem.LOCALLY_COMMISSIONED
        self.test_problem.save()
        self.assertEqual(self.test_problem.time_to_address, None)


class ProblemModelConcurrencyTests(TransactionTestCase, ConcurrencyTestMixin):

    def setUp(self):

        # The ConcurrencyTestMixin uses the deprecated get_revision_of_object
        # method triggering DeprecationWarning's. We switch these off here and
        # then reset the filters in the tearDown.
        #
        # Have reported as an issue: https://github.com/saxix/django-concurrency/issues/9
        #
        warnings.filterwarnings(
            "ignore",
            category=DeprecationWarning,
            module='concurrency.utils'
        )

        self.test_organisation = create_test_organisation()
        # These are needed for ConcurrencyTestMixin to run its' tests
        self.concurrency_model = Problem
        self.concurrency_kwargs = {'organisation': self.test_organisation,
                                   'description': 'A Test Problem',
                                   'category': 'cleanliness',
                                   'reporter_name': 'Test User',
                                   'reporter_email': 'reporter@example.com',
                                   'reporter_phone': '01111 111 111',
                                   'public': True,
                                   'public_reporter_name': True,
                                   'preferred_contact_method': Problem.CONTACT_EMAIL,
                                   'status': Problem.NEW}

    def tearDown(self):
        # get rid of filters added in setUp
        warnings.resetwarnings()


class ManagerTest(TestCase):

    def compare_querysets(self, actual, expected):
        for instance in expected:
            self.assertTrue(instance in actual, "Missing {0} '{1}' from actual".format(instance, instance.description))
        for instance in actual:
            self.assertTrue(instance in expected, "Missing {0} '{1}' from actual".format(instance, instance.description))


class ProblemManagerTests(ManagerTest):

    def setUp(self):
        self.test_organisation = create_test_organisation()

        # Brand new problems
        self.new_public_unmoderated_problem = create_test_problem({
            'description': 'new_public_unmoderated_problem',
            'organisation': self.test_organisation,
            'publication_status': Problem.NOT_MODERATED,
            'public': True
        })
        self.new_private_unmoderated_problem = create_test_problem({
            'description': 'new_private_unmoderated_problem',
            'organisation': self.test_organisation,
            'publication_status': Problem.NOT_MODERATED,
            'public': False
        })

        # Problems that have been closed before being moderated
        self.closed_public_unmoderated_problem = create_test_problem({
            'description': 'closed_public_unmoderated_problem',
            'organisation': self.test_organisation,
            'publication_status': Problem.NOT_MODERATED,
            'public': True,
            'status': Problem.RESOLVED
        })
        self.closed_private_unmoderated_problem = create_test_problem({
            'description': 'closed_private_unmoderated_problem',
            'organisation': self.test_organisation,
            'publication_status': Problem.NOT_MODERATED,
            'public': False,
            'status': Problem.RESOLVED
        })

        # Problems that have been moderated
        self.new_public_rejected_problem = create_test_problem({
            'description': 'new_public_rejected_problem',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.REJECTED
        })
        self.new_public_moderated_problem_published = create_test_problem({
            'description': 'new_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED
        })
        self.new_private_rejected_problem = create_test_problem({
            'description': 'new_private_rejected_problem',
            'organisation': self.test_organisation,
            'public': False,
            'publication_status': Problem.REJECTED
        })
        self.new_private_moderated_problem_published = create_test_problem({
            'description': 'new_private_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': False,
            'publication_status': Problem.PUBLISHED
        })

        # Problems that have been closed and moderated
        self.closed_public_rejected_problem = create_test_problem({
            'description': 'closed_public_rejected_problem',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.REJECTED,
            'status': Problem.RESOLVED
        })
        self.closed_public_moderated_problem_published = create_test_problem({
            'description': 'closed_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.RESOLVED
        })
        self.closed_private_rejected_problem = create_test_problem({
            'description': 'closed_private_rejected_problem',
            'organisation': self.test_organisation,
            'public': False,
            'publication_status': Problem.REJECTED,
            'status': Problem.RESOLVED
        })
        self.closed_private_moderated_problem_published = create_test_problem({
            'description': 'closed_private_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': False,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.RESOLVED
        })

        # Problems that have been escalated and moderated
        self.escalated_public_moderated_problem_published = create_test_problem({
            'description': 'escalated_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.ESCALATED,
            'commissioned': Problem.LOCALLY_COMMISSIONED,
        })

        self.escalated_acknowledged_public_moderated_problem_published = create_test_problem({
            'description': 'escalated_acknowledged_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.ESCALATED_ACKNOWLEDGED,
            'commissioned': Problem.LOCALLY_COMMISSIONED,
        })

        self.escalated_resolved_public_moderated_problem_published = create_test_problem({
            'description': 'escalated_resolved_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.ESCALATED_RESOLVED,
            'commissioned': Problem.LOCALLY_COMMISSIONED,
        })

        # Unmoderated escalated problems
        self.escalated_private_unmoderated_problem = create_test_problem({
            'description': 'escalated_private_unmoderated_problem',
            'organisation': self.test_organisation,
            'public': False,
            'status': Problem.ESCALATED,
            'commissioned': Problem.LOCALLY_COMMISSIONED,
        })

        # A breach of care standards problem
        self.breach_public_moderated_problem_published = create_test_problem({
            'description': 'breach_public_moderated_problem_published',
            'organisation': self.test_organisation,
            'public': True,
            'status': Problem.ACKNOWLEDGED,
            'breach': True,
            'publication_status': Problem.PUBLISHED
        })

        # Problems requiring second tier moderation
        self.public_problem_requiring_second_tier_moderation = create_test_problem({
            'description': 'public_problem_requiring_second_tier_moderation',
            'organisation': self.test_organisation,
            'public': True,
            'requires_second_tier_moderation': True,
            'publication_status': Problem.NOT_MODERATED
        })
        self.private_problem_requiring_second_tier_moderation = create_test_problem({
            'description': 'private_problem_requiring_second_tier_moderation',
            'organisation': self.test_organisation,
            'public': False,
            'requires_second_tier_moderation': True,
            'publication_status': Problem.NOT_MODERATED
        })

        # Problems in hidden statuses

        self.public_published_abusive_problem = create_test_problem({
            'description': 'public_published_abusive_problem',
            'organisation': self.test_organisation,
            'public': True,
            'publication_status': Problem.PUBLISHED,
            'status': Problem.ABUSIVE
        })

        # Intermediate helper lists
        self.open_unmoderated_problems = [self.new_public_unmoderated_problem,
                                          self.new_private_unmoderated_problem,
                                          self.escalated_private_unmoderated_problem]
        self.closed_unmoderated_problems = [self.closed_public_unmoderated_problem,
                                            self.closed_private_unmoderated_problem]
        self.open_moderated_problems = [self.new_public_rejected_problem,
                                        self.new_public_moderated_problem_published,
                                        self.new_private_rejected_problem,
                                        self.new_private_moderated_problem_published,
                                        self.escalated_public_moderated_problem_published,
                                        self.escalated_acknowledged_public_moderated_problem_published,
                                        self.public_problem_requiring_second_tier_moderation,
                                        self.private_problem_requiring_second_tier_moderation,
                                        self.breach_public_moderated_problem_published]
        self.closed_problems = self.closed_unmoderated_problems + [self.closed_public_rejected_problem,
                                                                   self.closed_public_moderated_problem_published,
                                                                   self.closed_private_rejected_problem,
                                                                   self.closed_private_moderated_problem_published,
                                                                   self.public_published_abusive_problem,
                                                                   self.escalated_resolved_public_moderated_problem_published]

        self.closed_resolved_problems = self.closed_unmoderated_problems + [self.closed_public_rejected_problem,
                                                                            self.closed_public_moderated_problem_published,
                                                                            self.closed_private_rejected_problem,
                                                                            self.closed_private_moderated_problem_published,
                                                                            self.public_published_abusive_problem,
                                                                            self.escalated_resolved_public_moderated_problem_published]

        # Lists that we expect from our manager's methods
        self.unmoderated_problems = self.open_unmoderated_problems + self.closed_unmoderated_problems
        self.open_problems = self.open_unmoderated_problems + self.open_moderated_problems
        self.open_published_visible_problems = [self.new_public_moderated_problem_published,
                                                          self.new_private_moderated_problem_published,
                                                          self.breach_public_moderated_problem_published]

        self.closed_published_visible_problems = [self.closed_public_moderated_problem_published,
                                                            self.closed_private_moderated_problem_published]

        self.all_problems = self.open_problems + self.closed_problems
        self.all_published_visible_problems = self.open_published_visible_problems + [self.closed_public_moderated_problem_published,
                                                                                      self.closed_private_moderated_problem_published]
        self.all_not_rejected_visible_problems = [
            self.new_public_unmoderated_problem,
            self.new_private_unmoderated_problem,
            self.closed_public_unmoderated_problem,
            self.closed_private_unmoderated_problem,
            self.new_public_moderated_problem_published,
            self.new_private_moderated_problem_published,
            self.closed_public_moderated_problem_published,
            self.closed_private_moderated_problem_published,
            self.breach_public_moderated_problem_published,

            # not shown as all escalated states are not visible, but will be when shown again. Sigh.
            # self.escalated_public_moderated_problem_published,
            # self.escalated_acknowledged_public_moderated_problem_published,
            # self.escalated_resolved_public_moderated_problem_published,
            # self.escalated_private_unmoderated_problem,
        ]

        self.problems_requiring_second_tier_moderation = [self.public_problem_requiring_second_tier_moderation,
                                                          self.private_problem_requiring_second_tier_moderation]

        self.open_escalated_problems = [self.escalated_public_moderated_problem_published,
                                        self.escalated_private_unmoderated_problem,
                                        self.escalated_acknowledged_public_moderated_problem_published]

    def test_all_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all(), self.all_problems)

    def test_open_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_problems(), self.open_problems)

    def test_closed_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.closed_problems(),
                               self.closed_resolved_problems)

    def test_unmoderated_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.unmoderated_problems(), self.unmoderated_problems)

    def test_open_published_visible_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_published_visible_problems(),
                               self.open_published_visible_problems)

    def test_closed_published_visible_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.closed_published_visible_problems(),
                               self.closed_published_visible_problems)

    def test_all_published_visible_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all_published_visible_problems(),
                               self.all_published_visible_problems)

    def test_all_not_rejected_visible_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.all_not_rejected_visible_problems(),
                               self.all_not_rejected_visible_problems)

    def test_problems_requiring_second_tier_moderation_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.problems_requiring_second_tier_moderation(),
                               self.problems_requiring_second_tier_moderation)

    def test_escalated_problems_returns_correct_problems(self):
        self.compare_querysets(Problem.objects.open_escalated_problems(),
                               self.open_escalated_problems)

    def test_requiring_survey_to_be_sent_returns_correct_problems(self):
        now = datetime.utcnow().replace(tzinfo=utc)
        survey_interval = timedelta(days=settings.SURVEY_INTERVAL_IN_DAYS)
        after_survey_cutoff = now - survey_interval + timedelta(days=1)

        old_problem = create_test_problem({
            'organisation': self.test_organisation,
            'created': after_survey_cutoff,
        })

        self.assertEqual(old_problem.created, after_survey_cutoff)

        # test that this problem does not need to be sent a survey
        self.assertEqual(Problem.objects.requiring_survey_to_be_sent().count(), 0)

        # change the created and check that it does
        old_problem.created = after_survey_cutoff - timedelta(days=2)
        old_problem.save()
        self.assertEqual(Problem.objects.requiring_survey_to_be_sent()[0].id, old_problem.id)

        # remove email address and check it does not need to be sent
        old_problem.reporter_email = ''
        old_problem.save()
        self.assertEqual(Problem.objects.requiring_survey_to_be_sent().count(), 0)

        # restore email address, mark as sent, check it does not need to be sent
        old_problem.email = 'foo@example.com'
        old_problem.survey_sent = now
        old_problem.save()
        self.assertEqual(Problem.objects.requiring_survey_to_be_sent().count(), 0)


class ProblemImageModelTests(ProblemImageTestBase):

    def setUp(self):
        # Create a test problem
        self.test_organisation = create_test_organisation()
        self.test_problem = create_test_problem({
            'organisation': self.test_organisation,
        })
        # The files are opened, but they need to be wrapped in Django's
        # file classes for the model to like them
        self.jpg = ImageFile(self.jpg)
        self.png = ImageFile(self.png)
        self.bmp = ImageFile(self.bmp)
        self.gif = ImageFile(self.gif)

    def test_can_create_image_for_problem(self):
        problem_image = ProblemImage(problem=self.test_problem)
        problem_image.image.save('test.jpg', self.jpg, save=True)

    def test_image_types_supported(self):
        problem_image = ProblemImage(problem=self.test_problem)
        for image_file in (self.jpg, self.png, self.bmp, self.gif):
            problem_image.image.save(image_file.name, image_file, save=True)

    def test_obfuscated_filenames(self):
        problem_image = ProblemImage(problem=self.test_problem)
        problem_image.image.save('test.jpg', self.jpg, save=True)

        # Note that django always divides FileField paths with unix separators
        expected_folder = 'images/' + strftime('%m_%Y', gmtime()) + '/'
        expected_filename_regex = re.compile(expected_folder + '[0-9a-f]{32}.jpg', re.I)
        self.assertRegexpMatches(problem_image.image.name, expected_filename_regex)

    @override_settings(MAX_IMAGES_PER_PROBLEM=1)
    def test_max_images(self):
        problem_image = ProblemImage(problem=self.test_problem)
        problem_image.image.save('test.jpg', self.jpg, save=True)

        with self.assertRaises(ValidationError) as context_manager:
            problem_image = ProblemImage(problem=self.test_problem)
            problem_image.image.save('test.jpg', self.jpg, save=True)

        self.assertEqual(len(context_manager.exception.messages), 1)
        self.assertEqual(context_manager.exception.messages[0], "Problems can only have a maximum of 1 images.")
