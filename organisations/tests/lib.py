from datetime import datetime, timedelta
from django.utils.timezone import utc

# Django imports
from django.test import TestCase

# App imports
from problems.models import Problem
from questions.models import Question
from organisations.lib import interval_counts

# Create a test instance of a Problem or Question model that will fill in
# default values for attributes not specified.
def create_test_instance(model, attributes):
    default_attributes = {'organisation_type': 'hospitals',
                          'choices_id': 33333,
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
        for age in problem_ages:
            created = now - timedelta(age)
            problem = create_test_instance(Problem, {'created': created})

    def test_interval_counts(self):
        problems = Problem.objects.all()
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'six_months': 6}
        self.assertEqual(expected_counts, interval_counts(problems))