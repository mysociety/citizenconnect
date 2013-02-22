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
    if 'organisation' not in attributes:
        # Make a dummy organisation
        attributes['organisation'] = create_test_organisation()
    default_attributes = {
        'organisation': None,
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
    # Override the created value to backdate the problem
    if 'created' in attributes:
        instance.created = attributes['created']
        instance.save()
    return instance

class IntervalCountsTest(TestCase):

    def create_problem(self, organisation, age):
        now = datetime.utcnow().replace(tzinfo=utc)
        created = now - timedelta(age)
        return create_test_instance(Problem, {'created': created,
                                              'organisation': organisation})

    def setUp(self):
        # Create a spread of problems over time
        problem_ages = [3, 4, 5, 21, 22, 45]
        self.test_organisation = create_test_organisation()
        self.other_test_organisation = create_test_organisation({'ods_code': 'ABC222',
                                                                 'name': 'Other Test Organisation'})
        for age in problem_ages:
            self.create_problem(self.test_organisation, age)
        other_problem_ages = [1, 2, 20, 65, 70]
        for age in other_problem_ages:
            self.create_problem(self.other_test_organisation, age)

    def test_organisation_interval_counts(self):
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'F84021',
                           'six_months': 6,
                           'all_time': 6}

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
                            'all_time': 5},
                           {'week': 3,
                           'four_weeks': 5,
                           'id': self.test_organisation.id,
                           'name': 'Test Organisation',
                           'ods_code': 'F84021',
                           'six_months': 6,
                           'all_time': 6}]
        self.assertEqual(expected_counts, interval_counts(issue_type=Problem,
                                                          filters={}))
