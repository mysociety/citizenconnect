from datetime import datetime, timedelta
from django.utils.timezone import utc

# Django imports
from django.test import TestCase

# App imports
from problems.models import Problem
from organisations.lib import interval_counts

class IntervalCountsTest(TestCase):

    def create_problem_with_created_datetime(self, created):
        problem = Problem(organisation_type='hospitals',
                          choices_id=33333,
                          description='A test problem',
                          category='cleanliness',
                          reporter_name='Test User',
                          reporter_email='reporter@example.com',
                          public=True,
                          public_reporter_name=True,
                          preferred_contact_method='email',
                          status=Problem.NEW
                          )
        problem.save()
        # Override the created value to backdate the problem
        problem.created = created
        problem.save()
        return problem

    def setUp(self):
        # Create a spread of problems over time
        now = datetime.utcnow().replace(tzinfo=utc)
        problem_ages = [3, 4, 5, 21, 22, 45]
        for age in problem_ages:
            created = now - timedelta(age)
            problem = self.create_problem_with_created_datetime(created)

    def test_interval_counts(self):
        problems = Problem.objects.all()
        expected_counts = {'week': 3,
                           'four_weeks': 5,
                           'six_months': 6}
        self.assertEqual(expected_counts, interval_counts(problems))
