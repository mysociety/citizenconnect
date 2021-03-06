import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal

# Django imports
from django.test import TestCase
from django.utils.timezone import utc
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem
from reviews_display.models import Review

from ..lib import interval_counts
from ..models import Organisation, Service, CCG, OrganisationParent

api_posting_id_counter = 328409234


def create_test_review(attributes={}):
    # Make a review

    global api_posting_id_counter
    api_posting_id_counter += 1

    organisation = attributes.get('organisation')
    del attributes['organisation']

    default_attributes = {'api_posting_id': str(api_posting_id_counter),
                          'api_postingorganisationid': '893470895',
                          'api_category': 'comment',
                          'author_display_name': 'A Test Author',
                          'title': 'A test title',
                          'content': 'Some test content'}
    default_attributes.update(attributes)
    instance = Review(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    instance.save()
    instance.organisations.add(organisation)
    return instance


def create_review_with_age(organisation, age, attributes={}):
    now = datetime.utcnow().replace(tzinfo=utc)
    published = now - timedelta(age)
    default_atts = {'api_published': published,
                    'api_updated': published,
                    'organisation': organisation}
    default_atts.update(attributes)
    return create_test_review(default_atts)


def create_test_ccg(attributes={}):
    # Make a CCG
    default_attributes = {
        'name': 'Test CCG',
        'code': 'CCG1',
        'email': 'test-ccg@example.org',
    }
    default_attributes.update(attributes)
    instance = CCG(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance


def create_test_organisation_parent(attributes={}):
    # Make an Organisation Parent
    default_attributes = {
        'name': 'Test Trust',
        'code': 'TRUST1',
        'choices_id': 1234,
        'email': 'test-trust@example.org',
        'secondary_email': 'test-trust-secondary@example.org',
    }
    default_attributes.update(attributes)
    if 'primary_ccg' not in attributes:
        default_attributes['primary_ccg'] = create_test_ccg({"code": default_attributes['code']})
    instance = OrganisationParent(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance


def create_test_organisation(attributes={}):
    # Make an organisation
    coords = {'lat': -0.06213,
              'lon': 51.536}
    default_attributes = {
        'name': 'Test Organisation',
        'organisation_type': 'gppractices',
        'choices_id': '12702',
        'ods_code': 'F84021',
        'point': Point(coords['lon'], coords['lat'])
    }
    default_attributes.update(attributes)
    if 'parent' not in attributes:
        default_attributes['parent'] = create_test_organisation_parent({'code': default_attributes['ods_code']})
    instance = Organisation(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance


def create_test_service(attributes={}):
    # Make a service
    default_attributes = {
        'name': 'Test Service',
        'service_code': 'SRV111',
    }
    default_attributes.update(attributes)
    instance = Service(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance


def create_test_problem(attributes={}):
    default_attributes = {
        'category': 'staff',
        'description': 'A test problem',
        'preferred_contact_method': 'email',
        'public': True,
        'public_reporter_name': True,
        'reporter_email': 'reporter@example.com',
        'reporter_name': 'Test User',
        'status': Problem.NEW,
    }
    default_attributes.update(attributes)

    # Add the organisation seperately as otherwise we end up with duplicate orgs
    # with the same ODS key.
    if 'organisation' not in default_attributes:
        default_attributes['organisation'] = create_test_organisation()

    problem = Problem(**dict((k, v) for (k, v) in default_attributes.items() if '__' not in k))
    problem.save()
    # Override the created value to backdate the issue
    if 'created' in attributes:
        problem.created = attributes['created']
        problem.save()
    return problem


def create_problem_with_age(organisation, age, attributes={}):
    now = datetime.utcnow().replace(tzinfo=utc)
    created = now - timedelta(age)
    default_atts = {'created': created,
                    'organisation': organisation}
    default_atts.update(attributes)
    return create_test_problem(default_atts)


# Auth helper methods
def get_reset_url_from_email(email):
    """
    Read the reset your password email and get the url from it, because we need
    the tokens it contains to check password resets properly
    Taken from https://github.com/django/django/blob/1.4.2/django/contrib/auth/tests/views.py
    """
    urlmatch = re.search(r".*/password-reset-confirm/([0-9A-Za-z]+)-(.+)", email.body)
    return urlmatch.groups()[0], urlmatch.groups()[1]


class IntervalCountsTest(TestCase):

    def setUp(self):
        self.test_ccg = create_test_ccg()
        self.other_test_ccg = create_test_ccg({'name': 'Other test ccg', 'code': 'CCG2'})

        self.test_trust = create_test_organisation_parent({'primary_ccg': self.test_ccg})
        self.test_trust.ccgs.add(self.test_ccg)
        self.test_trust.save()

        self.test_gp_surgery = create_test_organisation_parent({'primary_ccg': self.other_test_ccg,
                                                  'code': 'TRUST2'})
        self.test_gp_surgery.ccgs.add(self.other_test_ccg)
        self.test_gp_surgery.save()

        self.test_hospital = create_test_organisation({'ods_code': 'XXX999',
                                                       'organisation_type': 'hospitals',
                                                       'parent': self.test_trust})
        self.test_gp_branch = create_test_organisation({'ods_code': 'ABC222',
                                                        'name': 'Test GP Branch',
                                                        'organisation_type': 'gppractices',
                                                        'parent': self.test_gp_surgery})

        self.test_org_injuries = create_test_service({"service_code": 'ABC123',
                                                      "organisation_id": self.test_hospital.id})

        # Create a spread of problems over time for two organisations
        problem_ages = {3: {'time_to_acknowledge': 24, 'time_to_address': 220},
                        4: {'time_to_acknowledge': 32, 'time_to_address': 102},
                        5: {'happy_outcome': True, 'happy_service': True, 'status': Problem.ABUSIVE},
                        21: {'happy_outcome': False, 'status': Problem.UNABLE_TO_RESOLVE},
                        22: {'service_id': self.test_org_injuries.id},
                        45: {'time_to_acknowledge': 12, 'time_to_address': 400}}

        for age, attributes in problem_ages.items():
            create_problem_with_age(self.test_hospital, age, attributes)
        other_problem_ages = {1: {},
                              2: {},
                              20: {},
                              65: {},
                              70: {}}
        for age, attributes in other_problem_ages.items():
            create_problem_with_age(self.test_gp_branch, age, attributes)

        # Create a similar spread of reviews
        review_ages = [6, 12, 13, 50, 55]

        for age in review_ages:
            create_review_with_age(self.test_hospital, age)

        self.rejected_problem = create_problem_with_age(self.test_hospital, 1, {'publication_status': Problem.REJECTED})

        # Issue 1130 - Replies were being counted as reviews when showing totals for organisations
        # This reply should not be counted, adding it broke all the review tests before we
        # fixed the issue
        self.review_reply = create_review_with_age(self.test_hospital, 5)
        self.review_reply.in_reply_to = Review.objects.all()[0]
        self.review_reply.save()

    def test_organisation_interval_counts(self):
        organisation_filters = {'organisation_id': self.test_hospital.id}
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}
        self.assertEqual(expected_counts, interval_counts(organisation_filters=organisation_filters))

    def test_overall_interval_counts(self):
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts()
        self.assertEqual(expected_counts, actual)

    def test_extra_organisation_data(self):
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'lon': 51.536000000000001,
                            'lat': -0.062129999999999998,
                            'type': 'GP',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'lon': 51.536000000000001,
                           'lat': -0.062129999999999998,
                           'type': 'Hospital',
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(extra_organisation_data=['coords', 'type'])
        self.assertEqual(expected_counts, actual)

    def test_problem_data_intervals(self):
        expected_counts = [{'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'all_time': 5,
                            'all_time_open': 5,
                            'all_time_closed': 0,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'all_time': 6,
                           'all_time_open': 4,
                           'all_time_closed': 2,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(data_intervals=['all_time', 'all_time_open', 'all_time_closed'])
        self.assertEqual(expected_counts, actual)

    def test_review_data_intervals(self):
        expected_counts = [{'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'reviews_week': 0,
                            'reviews_four_weeks': 0,
                            'reviews_six_months': 0,
                            'reviews_all_time': 0},
                           {'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'reviews_week': 1,
                           'reviews_four_weeks': 3,
                           'reviews_six_months': 5,
                           'reviews_all_time': 5}]
        actual = interval_counts(data_intervals=['week', 'four_weeks', 'six_months', 'all_time'],
                                 data_type='reviews')
        self.assertEqual(expected_counts, actual)

    def test_filter_by_service_code(self):
        problem_filters = {'service_code': 'ABC123'}
        threshold = ['six_months', 1]
        expected_counts = [{'week': 0,
                           'four_weeks': 1,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 1,
                           'all_time': 1,
                           'happy_outcome': None,
                           'happy_service': None,
                           'average_time_to_acknowledge': None,
                           'average_time_to_address': None}]
        self.assertEqual(expected_counts, interval_counts(problem_filters=problem_filters, threshold=threshold))

    def test_filter_by_organisation_type(self):
        organisation_filters = {'organisation_type': 'gppractices'}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None}]
        self.assertEqual(expected_counts, interval_counts(organisation_filters=organisation_filters))

    def test_filter_by_statuses(self):
        problem_filters = {'status': (Problem.UNABLE_TO_RESOLVE, Problem.ABUSIVE,)}
        expected_counts = [{'week': 1,
                           'four_weeks': 2,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 2,
                           'all_time': 2,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': None,
                           'average_time_to_address': None}]
        actual = interval_counts(problem_filters=problem_filters, threshold=['six_months', 1])
        self.assertEqual(expected_counts, actual)

    def test_filter_by_ccg(self):
        organisation_filters = {'ccg': self.other_test_ccg.id}
        # Stolen from test_filter_by_organisation_type, luckily
        # the other org is in a different ccg to test_organisation, so I don't
        # have to work all this out
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None}]
        actual = interval_counts(organisation_filters=organisation_filters)
        self.assertEqual(expected_counts, actual)

    def test_filter_by_breach_filter(self):
        self._test_filter_by_bool_filters('breach')

    def test_filter_by_formal_complaint_filter(self):
        self._test_filter_by_bool_filters('formal_complaint')

    def _test_filter_by_bool_filters(self, filter):
        # Add some specific breach problems in for self.test_hospital
        create_problem_with_age(self.test_hospital, 1, {filter: True})
        create_problem_with_age(self.test_hospital, 10, {filter: True})
        create_problem_with_age(self.test_hospital, 100, {filter: True})
        create_problem_with_age(self.test_hospital, 365, {filter: True})
        problem_filters = {filter: True}
        threshold = ['six_months', 1]
        expected_counts = [{'week': 1,
                            'four_weeks': 2,
                            'id': self.test_hospital.id,
                            'name': self.test_hospital.name,
                            'ods_code': self.test_hospital.ods_code,
                            'six_months': 3,
                            'all_time': 4,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None}]
        actual = interval_counts(problem_filters=problem_filters, threshold=threshold)
        self.assertEqual(expected_counts, actual)

        problem_filters = {filter: False}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(problem_filters=problem_filters, threshold=threshold)
        self.assertEqual(expected_counts, actual)

    def test_applies_interval_count_threshold_to_overall_counts(self):
        expected_counts = [{'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(threshold=('six_months', 6))
        self.assertEqual(expected_counts, actual)

    def test_applies_all_time_interval_count_threshold_to_overall_counts(self):
        expected_counts = [{'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(threshold=('all_time', 6))
        self.assertEqual(expected_counts, actual)

    def test_filtering_with_organisation_ids(self):
        organisation_filters = {'organisation_ids': (self.test_gp_branch.id, self.test_hospital.id)}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.test_gp_branch.id,
                            'name': self.test_gp_branch.name,
                            'ods_code': self.test_gp_branch.ods_code,
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_hospital.id,
                           'name': self.test_hospital.name,
                           'ods_code': self.test_hospital.ods_code,
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(organisation_filters=organisation_filters)
        self.assertEqual(expected_counts, actual)

    def test_errors_on_empty_organisation_ids(self):
        # Bug #897 - When passed an empty array of organisation_ids the code
        # tried to use them, resulting in an SQL error, so now it should check
        # and raise a more suitable error
        organisation_filters = {'organisation_ids': ()}
        with self.assertRaises(ValueError) as context_manager:
            interval_counts(organisation_filters=organisation_filters)

    def test_counts_ordered_by_name_and_ods_code(self):
        # Bug #1167 - When two orgs have the same name, the problem count
        # appeared against the wrong organisation. interval_counts wasn't really
        # the culprit, rather some code in the view which assumed separate calls for
        # reviews and problems would always be sorted the same, when really
        # the DB could not be relied upon for this, so we changed the ordering
        # to also order by ods_code after name.

        # Add a new hospital with the same name as the existing one
        duplicate_name_hospital = create_test_organisation({
            'ods_code': 'XXX888',
            'organisation_type': 'hospitals',
            'parent': self.test_trust,
            'name': self.test_hospital.name
        })

        counts = interval_counts()

        self.assertEqual(counts[0]['ods_code'], self.test_gp_branch.ods_code)
        self.assertEqual(counts[1]['ods_code'], duplicate_name_hospital.ods_code)
        self.assertEqual(counts[2]['ods_code'], self.test_hospital.ods_code)


class AuthorizationTestCase(TestCase):
    """
    A test case which sets up some dummy data useful for testing authorization
    """

    fixtures = ['development_users.json']

    def setUp(self):
        # Create some dummy Users and an Organisation they want to access

        # CCGs
        self.test_ccg = create_test_ccg()
        self.other_test_ccg = create_test_ccg({'name': 'other test ccg', 'code': 'XYZ'})

        # Organisation Parent
        self.test_trust = create_test_organisation_parent({'primary_ccg': self.test_ccg})
        self.test_gp_surgery = create_test_organisation_parent({'name': 'other test trust',
                                                                'code': 'XYZ',
                                                                'primary_ccg': self.other_test_ccg})

        self.test_trust.ccgs.add(self.test_ccg)
        self.test_trust.save()
        self.test_gp_surgery.ccgs.add(self.other_test_ccg)
        self.test_gp_surgery.save()

        # Organisations
        self.test_hospital = create_test_organisation({'organisation_type': 'hospitals',
                                                       'parent': self.test_trust,
                                                       'point': Point(-0.2, 51.5)})
        self.test_gp_branch = create_test_organisation({'ods_code': '12345',
                                                        'name': 'Test GP Branch',
                                                        'parent': self.test_gp_surgery,
                                                        'point': Point(-0.1, 51.5)})

        # Users
        self.test_password = 'password'

        # A user that is allowed to access the test trust
        self.trust_user = User.objects.get(pk=6)
        # add the relation to the trust
        self.test_trust.users.add(self.trust_user)
        self.test_trust.save()

        # A Django superuser
        self.superuser = User.objects.get(pk=1)

        # An anonymous user
        self.anonymous_user = AnonymousUser()

        # A trust user linked to no trusts
        self.no_trust_user = User.objects.get(pk=8)

        # A User linked to the test gp surgery
        self.gp_surgery_user = User.objects.get(pk=7)
        # add the relation to the other trust
        self.test_gp_surgery.users.add(self.gp_surgery_user)
        self.test_gp_surgery.save()

        # An NHS Superuser
        self.nhs_superuser = User.objects.get(pk=4)

        # A Case Handler
        self.case_handler = User.objects.get(pk=3)

        # A Second Tier Moderator
        self.second_tier_moderator = User.objects.get(pk=12)

        # A CCG user linked to no CCGs
        self.no_ccg_user = User.objects.get(pk=14)

        # A CCG user for the CCG that test trust belongs to
        self.ccg_user = User.objects.get(pk=9)
        self.test_ccg.users.add(self.ccg_user)
        self.test_ccg.save()

        # A CCG user for the CCG that gp surgery belongs to
        self.other_ccg_user = User.objects.get(pk=13)
        self.other_test_ccg.users.add(self.other_ccg_user)
        self.other_test_ccg.save()

        # Helpful lists for simpler testing
        self.users_who_can_access_everything = [self.superuser, self.nhs_superuser]

        # Reference to the login url because lots of tests need it
        self.login_url = reverse('login')

        # Turn off logging in the tests because almost every authorization test
        # creates noisy "Permission Denied" errors which will get printed
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Turn logging back on
        logging.disable(logging.NOTSET)

    def login_as(self, user):
        logged_in = self.client.login(username=user.username, password=self.test_password)
        self.assertTrue(logged_in)
