from datetime import datetime, timedelta

# Django imports
from django.test import TestCase
from django.conf import settings
from django.utils.timezone import utc
from django.contrib.gis.geos import Point

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
        problem_ages = {3: {'acknowledged_in_time' : False, 'addressed_in_time': True},
                        4: {'acknowledged_in_time' : True, 'addressed_in_time': False},
                        5: {'happy_outcome': True, 'happy_service': True},
                        21: {'happy_outcome': False},
                        22: {'service_id': self.test_org_injuries.id},
                        45: {'acknowledged_in_time' : True, 'addressed_in_time': False}}

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
                           'acknowledged_in_time': 0.66666666666666696,
                           'acknowledged_in_time_count': 3,
                           'addressed_in_time': 0.33333333333333298,
                           'addressed_in_time_count': 3}

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
                            'acknowledged_in_time': None,
                            'acknowledged_in_time_count': 0,
                            'addressed_in_time': None,
                            'addressed_in_time_count': 0},
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
                           'acknowledged_in_time': 0.66666666666666696,
                           'acknowledged_in_time_count': 3,
                           'addressed_in_time': 0.33333333333333298,
                           'addressed_in_time_count': 3}]
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
                           'acknowledged_in_time': None,
                           'acknowledged_in_time_count': 0,
                           'addressed_in_time': None,
                           'addressed_in_time_count': 0}]
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
                            'acknowledged_in_time': None,
                            'acknowledged_in_time_count': 0,
                            'addressed_in_time': None,
                            'addressed_in_time_count': 0 }]
        self.assertEqual(expected_counts, interval_counts(issue_type=Problem,
                                                          filters=filters))
