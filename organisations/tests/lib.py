import logging
import re
from datetime import datetime, timedelta
from decimal import Decimal

# Django imports
from django.test import TestCase
from django.conf import settings
from django.utils.timezone import utc
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User, AnonymousUser, Group
from django.core.urlresolvers import reverse

# App imports
from issues.models import Problem

from ..lib import interval_counts
from ..models import Organisation, Service, CCG

def create_test_ccg(attributes={}):
    # Make a CCG
    default_attributes = {
        'name':'Test CCG',
        'code':'ABC',
        'email': 'test-ccg@example.org',
    }
    default_attributes.update(attributes)
    instance = CCG(**dict((k,v) for (k,v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance

def create_test_organisation(attributes={}):
    # Make an organisation
    coords = {'lat': -0.06213,
              'lon': 51.536}
    default_attributes = {
        'name':'Test Organisation',
        'organisation_type':'gppractices',
        'choices_id':'12702',
        'ods_code':'F84021',
        'point': Point(coords['lon'], coords['lat'])
    }
    default_attributes.update(attributes)
    if 'escalation_ccg' not in attributes:
        default_attributes['escalation_ccg'] = create_test_ccg({"code": default_attributes['ods_code']})
    instance = Organisation(**dict((k,v) for (k,v) in default_attributes.items() if '__' not in k))
    instance.save()
    return instance

def create_test_service(attributes={}):
    # Make a service
    default_attributes = {
        'name': 'Test Service',
        'service_code': 'SRV111',
    }
    default_attributes.update(attributes)
    instance = Service(**dict((k,v) for (k,v) in default_attributes.items() if '__' not in k))
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

    problem = Problem(**dict((k,v) for (k,v) in default_attributes.items() if '__' not in k))
    problem.save()
    # Override the created value to backdate the issue
    if 'created' in attributes:
        problem.created = attributes['created']
        problem.save()
    return problem

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

    def create_problem(self, organisation, age, attributes={}):
        now = datetime.utcnow().replace(tzinfo=utc)
        created = now - timedelta(age)
        default_atts = {'created': created,
                        'organisation': organisation}
        default_atts.update(attributes)
        return create_test_problem(default_atts)

    def setUp(self):
        self.test_ccg = create_test_ccg()
        self.other_test_ccg = create_test_ccg({'name': 'Other test ccg', 'code': 'DEF'})
        self.test_organisation = create_test_organisation({'ods_code': 'XXX999',
                                                           'organisation_type': 'hospitals'})
        self.test_organisation.ccgs.add(self.test_ccg)
        self.test_organisation.save()
        self.other_test_organisation = create_test_organisation({'ods_code': 'ABC222',
                                                                 'name': 'Other Test Organisation',
                                                                 'organisation_type': 'gppractices'})
        self.other_test_organisation.ccgs.add(self.other_test_ccg)
        self.other_test_organisation.save()
        self.test_org_injuries = create_test_service({"service_code": 'ABC123',
                                                      "organisation_id": self.test_organisation.id})
        # Create a spread of problems over time for two organisations
        problem_ages = {3: {'time_to_acknowledge' : 24, 'time_to_address': 220},
                        4: {'time_to_acknowledge' : 32, 'time_to_address': 102},
                        5: {'happy_outcome': True, 'happy_service': True, 'status': Problem.ABUSIVE},
                        21: {'happy_outcome': False, 'status': Problem.UNABLE_TO_RESOLVE},
                        22: {'service_id': self.test_org_injuries.id},
                        45: {'time_to_acknowledge' : 12, 'time_to_address': 400}}

        for age, attributes in problem_ages.items():
            self.create_problem(self.test_organisation, age, attributes)
        other_problem_ages = {1: {},
                              2: {},
                              20: {},
                              65: {},
                              70: {}}
        for age, attributes in other_problem_ages.items():
            self.create_problem(self.other_test_organisation, age, attributes)

    def test_organisation_interval_counts(self):
        organisation_filters = {'organisation_id': self.test_organisation.id}
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
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
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
        expected_counts = [{'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'all_time': 5,
                            'all_time_open': 5,
                            'all_time_closed': 0,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
                           'all_time': 6,
                           'all_time_open': 4,
                           'all_time_closed': 2,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(problem_data_intervals=['all_time', 'all_time_open', 'all_time_closed'])
        self.assertEqual(expected_counts, actual)


    def test_filter_by_service_code(self):
        problem_filters = {'service_code': 'ABC123'}
        threshold=['six_months', 1]
        expected_counts = [{'week': 0,
                           'four_weeks': 1,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None }]
        self.assertEqual(expected_counts, interval_counts(organisation_filters=organisation_filters))

    def test_filter_by_statuses(self):
        problem_filters = {'status': (Problem.UNABLE_TO_RESOLVE, Problem.ABUSIVE,)}
        expected_counts = [{'week': 1,
                           'four_weeks': 2,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None }]
        actual = interval_counts(organisation_filters=organisation_filters)
        self.assertEqual(expected_counts, actual)

    def test_filter_by_breach(self):
        # Add some specific breach problems in for self.test_organisation
        self.create_problem(self.test_organisation, 1, {'breach': True})
        self.create_problem(self.test_organisation, 10, {'breach': True})
        self.create_problem(self.test_organisation, 100, {'breach': True})
        self.create_problem(self.test_organisation, 365, {'breach': True})
        problem_filters = {'breach': True}
        threshold=['six_months', 1]
        expected_counts = [{'week': 1,
                            'four_weeks': 2,
                            'id': self.test_organisation.id,
                            'name': 'Test Organisation',
                            'ods_code': 'XXX999',
                            'six_months': 3,
                            'all_time': 4,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None }]
        actual = interval_counts(problem_filters=problem_filters, threshold=threshold)
        self.assertEqual(expected_counts, actual)

        problem_filters = {'breach': False}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
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
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(threshold=('all_time', 6))
        self.assertEqual(expected_counts, actual)

    def test_filtering_with_organisation_ids(self):
        organisation_filters = {'organisation_ids': (self.other_test_organisation.id,self.test_organisation.id)}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_service': None,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_service': 1.0,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(organisation_filters=organisation_filters)
        self.assertEqual(expected_counts, actual)

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

        # Organisations
        self.test_organisation = create_test_organisation({'organisation_type': 'hospitals',
                                                           'escalation_ccg': self.test_ccg})
        self.test_organisation.ccgs.add(self.test_ccg)
        self.other_test_organisation = create_test_organisation({'ods_code': '12345',
                                                                 'name': 'Other Test Organisation',
                                                                 'escalation_ccg': self.other_test_ccg})
        self.other_test_organisation.ccgs.add(self.other_test_ccg)

        self.test_password = 'password'

        # A user that is allowed to access the organisation
        self.provider = User.objects.get(pk=6)
        # add the relation to the organisation
        self.test_organisation.users.add(self.provider)
        self.test_organisation.save()

        # A Django superuser
        self.superuser = User.objects.get(pk=1)

        # An anonymous user
        self.anonymous_user = AnonymousUser()

        # A provider user linked to no providers
        self.no_provider = User.objects.get(pk=8)

        # A User linked to a different provider
        self.other_provider = User.objects.get(pk=7)
        # add the relation to the other organisation
        self.other_test_organisation.users.add(self.other_provider)
        self.other_test_organisation.save()

        # A user linked to multiple providers
        self.pals = User.objects.get(pk=2)
        self.test_organisation.users.add(self.pals)
        self.test_organisation.save()
        self.other_test_organisation.users.add(self.pals)
        self.other_test_organisation.save()

        # An NHS Superuser
        self.nhs_superuser = User.objects.get(pk=4)

        # A Case Handler
        self.case_handler = User.objects.get(pk=3)

        # A Second Tier Moderator
        self.second_tier_moderator = User.objects.get(pk=12)

        # A CCG user linked to no CCGs
        self.no_ccg_user = User.objects.get(pk=14)

        # A CCG user for the CCG that test organisation belongs to
        self.ccg_user = User.objects.get(pk=9)
        self.test_ccg.users.add(self.ccg_user)
        self.test_ccg.save()

        # A CCG user for the CCG that other test organisation belongs to
        self.other_ccg_user = User.objects.get(pk=13)
        self.other_test_ccg.users.add(self.other_ccg_user)
        self.other_test_ccg.save()

        # A Customer Contact Centre user
        self.customer_contact_centre_user = User.objects.get(pk=15)

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
