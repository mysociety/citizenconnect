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

    def setUp(self):
        # Create a spread of problems over time
        now = datetime.utcnow().replace(tzinfo=utc)
        problem_ages = [3, 4, 5, 21, 22, 45]
        test_organisation = create_test_organisation()
        for age in problem_ages:
            created = now - timedelta(age)
            problem = create_test_instance(Problem, {'created': created, 'organisation': test_organisation})

    def test_interval_counts(self):
        problems = Problem.objects.all()
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'six_months': 6,
                           'all_time': 6}
        self.assertEqual(expected_counts, interval_counts(problems))
