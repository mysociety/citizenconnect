from datetime import datetime, timedelta
from decimal import Decimal

# Django imports
from django.test import TestCase
from django.conf import settings
from django.utils.timezone import utc
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User, AnonymousUser, Group

# App imports
from issues.models import Problem, Question

from ..lib import interval_counts
from ..models import Organisation, Service

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

# Create a test instance of a Problem or Question model that will fill in
# default values for attributes not specified.
def create_test_instance(model, attributes):
    # Problems need an organisations
    if model == Problem and 'organisation' not in attributes:
        # Make a dummy organisation
        attributes['organisation'] = create_test_organisation()

    default_attributes = {
        'description': 'A test problem',
        'category': 'staff',
        'reporter_name': 'Test User',
        'reporter_email': 'reporter@example.com',
        'public': True,
        'public_reporter_name': True,
        'preferred_contact_method': 'email',
        'status': model.NEW
    }
    default_attributes.update(attributes)
    instance = model(**dict((k,v) for (k,v) in default_attributes.items() if '__' not in k))
    instance.save()
    # Override the created value to backdate the issue
    if 'created' in attributes:
        instance.created = attributes['created']
        instance.save()
    return instance

class IntervalCountsTest(TestCase):

    def create_problem(self, organisation, age, attributes={}):
        now = datetime.utcnow().replace(tzinfo=utc)
        created = now - timedelta(age)
        default_atts = {'created': created,
                        'organisation': organisation}
        default_atts.update(attributes)
        return create_test_instance(Problem, default_atts)

    def setUp(self):
        self.test_organisation = create_test_organisation({'ods_code': 'XXX999',
                                                           'organisation_type': 'hospital'})
        self.other_test_organisation = create_test_organisation({'ods_code': 'ABC222',
                                                                 'name': 'Other Test Organisation',
                                                                 'organisation_type': 'gppractices'})
        self.test_org_injuries = create_test_service({"service_code": 'ABC123',
                                                      "organisation_id": self.test_organisation.id})
        # Create a spread of problems over time for two organisations
        problem_ages = {3: {'time_to_acknowledge' : 24, 'time_to_address': 220},
                        4: {'time_to_acknowledge' : 32, 'time_to_address': 102},
                        5: {'happy_outcome': True, 'happy_service': True},
                        21: {'happy_outcome': False},
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
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
                           'six_months': 6,
                           'all_time': 6,
                           'happy_outcome': 0.5,
                           'happy_outcome_count': 2,
                           'happy_service': 1.0,
                           'happy_service_count': 1,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}
        self.assertEqual(expected_counts, interval_counts(issue_type=Problem,
                                                          filters={},
                                                          organisation_id=self.test_organisation.id))

    def test_overall_interval_counts(self):
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_outcome_count': 0,
                            'happy_service': None,
                            'happy_service_count': 0,
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
                           'happy_outcome_count': 2,
                           'happy_service': 1.0,
                           'happy_service_count': 1,
                           'average_time_to_acknowledge': Decimal('22.6666666666666667'),
                           'average_time_to_address': Decimal('240.6666666666666667')}]
        actual = interval_counts(issue_type=Problem, filters={})
        self.assertEqual(expected_counts, actual)

    def test_filter_by_service_code(self):
        filters = {'service_code': 'ABC123'}
        expected_counts = [{'week': 0,
                           'four_weeks': 1,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'XXX999',
                           'six_months': 1,
                           'all_time': 1,
                           'happy_outcome': None,
                           'happy_outcome_count': 0,
                           'happy_service': None,
                           'happy_service_count': 0,
                           'average_time_to_acknowledge': None,
                           'average_time_to_address': None}]
        self.assertEqual(expected_counts, interval_counts(issue_type=Problem,
                                                          filters=filters))

    def test_filter_by_organisation_type(self):
        filters = {'organisation_type': 'gppractices'}
        expected_counts = [{'week': 2,
                            'four_weeks': 3,
                            'id': self.other_test_organisation.id,
                            'name': 'Other Test Organisation',
                            'ods_code': 'ABC222',
                            'six_months': 5,
                            'all_time': 5,
                            'happy_outcome': None,
                            'happy_outcome_count': 0,
                            'happy_service': None,
                            'happy_service_count': 0,
                            'average_time_to_acknowledge': None,
                            'average_time_to_address': None }]
        self.assertEqual(expected_counts, interval_counts(issue_type=Problem,
                                                          filters=filters))

class AuthorizationTestCase(TestCase):
    """
    A test case which sets up some dummy data useful for testing authorization
    """

    def setUp(self):
        # Create some dummy Users and an Organisation they want to access

        # Organisations
        self.test_organisation = create_test_organisation()
        self.other_test_organisation = create_test_organisation({'ods_code': 12345})

        providers_group = Group.objects.get(pk=Organisation.PROVIDERS)

        # A user that is allowed to access the organisation
        self.test_password = 'password'
        self.test_allowed_user = User.objects.create_user('Test User',
                                                          'user@example.com',
                                                          self.test_password)
        self.test_allowed_user.groups.add(providers_group)
        self.test_allowed_user.save()
        # add the relation to the organisation
        self.test_organisation.users.add(self.test_allowed_user)
        self.test_organisation.save()

        # A Django superuser
        self.superuser = User.objects.create_superuser('Super User',
                                                       'superuser@example.com',
                                                       self.test_password)

        # An anonymous user
        self.anonymous_user = AnonymousUser()

        # A provider user linked to no providers
        self.test_no_provider_user = User.objects.create_user('Test No Provider User',
                                                              'noprovideruser@example.com',
                                                              self.test_password)
        self.test_no_provider_user.groups.add(providers_group)
        self.test_no_provider_user.save()

        # A User linked to a different provider
        self.test_other_provider_user = User.objects.create_user('Test Other Provider User',
                                                                 'otherprovideruser@example.com',
                                                                 self.test_password)
        self.test_other_provider_user.groups.add(providers_group)
        self.test_other_provider_user.save()
        # add the relation to the other organisation
        self.other_test_organisation.users.add(self.test_other_provider_user)
        self.other_test_organisation.save()

        # A user linked to multiple providers
        self.test_pals_user = User.objects.create_user('Test Multiple Provider User',
                                                       'multipleprovideruser@example.com',
                                                       self.test_password)
        self.test_organisation.users.add(self.test_pals_user)
        self.test_organisation.save()
        self.other_test_organisation.users.add(self.test_pals_user)
        self.other_test_organisation.save()

        # An NHS Superuser
        self.test_nhs_superuser = User.objects.create_user('Test NHS Super User',
                                                           'nhssuperuser@example.com',
                                                           self.test_password)
        nhs_superusers_group = Group.objects.get(pk=Organisation.NHS_SUPERUSERS)
        self.test_nhs_superuser.groups.add(nhs_superusers_group)
        self.test_nhs_superuser.save()

        # A Moderator
        self.test_moderator = User.objects.create_user('Test Moderator',
                                                        'moderator@example.com',
                                                        self.test_password)
        moderators_group = Group.objects.get(pk=Organisation.MODERATORS)
        self.test_moderator.groups.add(moderators_group)
        self.test_moderator.save()

        # Helpful lists for simpler testing
        self.users_who_can_access_everything = [self.superuser, self.test_nhs_superuser, self.test_moderator]

        # Turn off logging in the tests because almost every authorization test
        # creates noisy "Permission Denied" errors which will get printed
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        # Turn logging back on
        logging.disable(logging.NOTSET)

    def login_as(self, user):
        logged_in = self.client.login(username=user.username, password=self.test_password)
        self.assertTrue(logged_in)