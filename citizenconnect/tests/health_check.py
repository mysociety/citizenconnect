from datetime import datetime, timedelta

import reversion

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.conf.locale.en_GB import formats
from django.template.defaultfilters import date as django_date

from organisations.tests.lib import (
    create_test_organisation,
    create_problem_with_age
)
from reviews_display.tests import create_test_review
from reviews_submit.tests import create_review
from issues.models import Problem


class HealthCheckTests(TestCase):

    def setUp(self):
        self.health_check_url = reverse('healthcheck')
        self.organisation = create_test_organisation()
        self.now = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.two_hours_ago = self.now - timedelta(hours=2)
        self.two_days_ago = self.now - timedelta(days=2)

    def test_no_problems(self):
        resp = self.client.get(self.health_check_url)
        self.assertEqual(resp.status_code, 200)

    def test_overdue_problem_emails(self):
        # Add a problem older than 2 hours that hasn't been mailed
        create_problem_with_age(self.organisation, 1)
        resp = self.client.get(self.health_check_url)
        self.assertContains(resp, '1 unsent problem - Bad', status_code=500)

    def test_overdue_confirmation_emails(self):
        # Add a problem older than 2 hours that hasn't had the confirmation
        # sent, but has been mailed.
        problem = create_problem_with_age(self.organisation, 1)
        problem.confirmation_required = True
        problem.mailed = True
        problem.save()
        resp = self.client.get(self.health_check_url)
        self.assertContains(resp, '1 unsent confirmation - Bad', status_code=500)

    def test_overdue_survey_emails(self):
        # Add a closed problem that has been mailed and the confirmation sent,
        # but hasn't had it's survey sent
        with reversion.create_revision():
            problem = create_problem_with_age(self.organisation, 1)
        problem.mailed = True
        problem.confirmation_sent = problem.created
        problem.status = Problem.RESOLVED
        with reversion.create_revision():
            problem.save()
        # This is a bit tricky, we need to alter the problem revisions so that
        # it looks like it was closed over two hours ago
        versions = list(reversion.get_for_object(problem).order_by("revision__date_created"))
        versions[0].revision.date_created = problem.created
        versions[0].revision.save()
        versions[1].revision.date_created = problem.created + timedelta(hours=1)
        versions[1].revision.save()

        resp = self.client.get(self.health_check_url)
        self.assertContains(resp, '1 unsent survey - Bad', status_code=500)

    def test_overdue_reviews(self):
        # Create a review which hasn't been sent to NHS Choices and is over
        # 2 hours old
        review = create_review(self.organisation)
        review.created = self.two_hours_ago
        review.last_sent_to_api = None
        review.save()
        resp = self.client.get(self.health_check_url)
        self.assertContains(resp, '1 unsent review - Bad', status_code=500)

    def test_no_reviews_from_choices_api(self):
        # Create a review from the Choices API that's over two days old, so
        # that it looks like nothing has been updated in a while
        review = create_test_review({'organisation': self.organisation})
        review.created = self.two_days_ago
        review.save()
        resp = self.client.get(self.health_check_url)
        expected_text = 'Last new review (from NHS Choices) created: {0} - Bad'.format(django_date(review.created, formats.DATETIME_FORMAT))
        self.assertContains(resp, expected_text, status_code=500)

    def test_no_new_problems_recently(self):
        # Create a problem but make it over 1 week old
        problem = create_problem_with_age(self.organisation, 8)
        resp = self.client.get(self.health_check_url)
        expected_text = 'Last new problem created: {0} - Bad'.format(django_date(problem.created, formats.DATETIME_FORMAT))
        self.assertContains(resp, expected_text, status_code=500)
