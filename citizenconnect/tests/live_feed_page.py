from datetime import timedelta, date

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.conf import settings
from django.template.defaultfilters import date as django_date
from django.template.defaultfilters import capfirst

from organisations.tests.lib import (
    create_test_problem,
    create_problem_with_age,
    create_review_with_age
)
from reviews_display.tests import create_test_review, create_test_organisation
from issues.models import Problem

@override_settings(LIVE_FEED_CUTOFF_DAYS=30, LIVE_FEED_PER_PAGE=25)
class LiveFeedTests(TestCase):

    def setUp(self):
        self.live_feed_url = reverse('live-feed', kwargs={'cobrand': 'choices'})
        self.organisation = create_test_organisation({})

    def test_empty_page(self):
        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, 'There are no matching problems or reviews, try expanding your date range or selecting a different organisation if you have chosen one.')

    def test_doesnt_show_replies(self):
        review = create_test_review({'organisation': self.organisation})
        reply = create_test_review({'organisation': self.organisation})
        reply.in_reply_to = review
        reply.save()
        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        reply_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': reply.api_posting_id,
                'ods_code': reply.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        resp = self.client.get(self.live_feed_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, reply_url)

    def test_limits_initial_results(self):
        problem = create_test_problem({'organisation': self.organisation})
        old_problem_date = timezone.now() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS + 1)
        old_problem = create_test_problem({
            'organisation': self.organisation,
            'created': old_problem_date
        })

        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, reverse(
                'problem-view',
                kwargs={'pk': problem.id, 'cobrand': 'choices'}
            )
        )
        self.assertNotContains(resp, reverse(
                'problem-view',
                kwargs={'pk': old_problem.id, 'cobrand': 'choices'}
            )
        )

    @override_settings(LIVE_FEED_CUTOFF_DAYS=2)
    def test_filters_by_date_range(self):
        # Make some test problems with varying dates
        problem = create_test_problem({'organisation': self.organisation})
        review = create_test_review({'organisation': self.organisation})

        now = timezone.now()

        old_problem = create_problem_with_age(self.organisation, 1)
        old_review = create_review_with_age(self.organisation, 1)
        older_problem = create_problem_with_age(self.organisation, 3)
        older_review = create_review_with_age(self.organisation, 3)

        # Get the urls for each, because that's the easiest bit of content to
        # look for in the page to see if they're filtered or not
        problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'choices'})
        old_problem_url = reverse('problem-view', kwargs={'pk': old_problem.id, 'cobrand': 'choices'})
        older_problem_url = reverse('problem-view', kwargs={'pk': older_problem.id, 'cobrand': 'choices'})
        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        old_review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': old_review.api_posting_id,
                'ods_code': old_review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        older_review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': older_review.api_posting_id,
                'ods_code': older_review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )

        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, old_problem_url)
        self.assertContains(resp, review_url)
        self.assertContains(resp, old_review_url)
        # LIVE_FEED_CUTOFF_DAYS should exclude this until we expand the date
        # range
        self.assertNotContains(resp, older_problem_url)
        self.assertNotContains(resp, older_review_url)

        # Extending the date range to four days should bring all the problems
        # in
        four_days_ago = now - timedelta(days=4)

        filtered_url_string = "{0}?start={1}%2F{2}%2F{3}&end={4}%2F{5}%2F{6}"
        filtered_url = filtered_url_string.format(
            self.live_feed_url,
            four_days_ago.day,
            four_days_ago.month,
            four_days_ago.year,
            now.day,
            now.month,
            now.year
        )

        resp = self.client.get(filtered_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, old_problem_url)
        self.assertContains(resp, older_problem_url)
        self.assertContains(resp, review_url)
        self.assertContains(resp, old_review_url)
        self.assertContains(resp, older_review_url)

        # Contracting the date range to 1 day should limit the problems again
        filtered_url = filtered_url_string.format(
            self.live_feed_url,
            now.day,
            now.month,
            now.year,
            now.day,
            now.month,
            now.year
        )

        resp = self.client.get(filtered_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, old_problem_url)
        self.assertNotContains(resp, older_problem_url)
        self.assertNotContains(resp, old_review_url)
        self.assertNotContains(resp, older_review_url)

    def test_date_filters_show_defaults(self):
        resp = self.client.get(self.live_feed_url)
        # the start_date should be showing whatever 30 days ago equates to
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        start_date_string = '<input type="text" name="start" value="{0}" id="id_start" />'
        end_date_string = '<input type="text" name="end" value="{0}" id="id_end" />'
        self.assertContains(resp, start_date_string.format(thirty_days_ago.strftime("%d/%m/%Y")))
        self.assertContains(resp, end_date_string.format(today.strftime("%d/%m/%Y")))

    def test_filters_by_organisation(self):
        # add a second organisation so that we can test filtering
        other_organisation = create_test_organisation({"ods_code": "OTHER"})

        # add some problems and reviews for each org
        problem = create_test_problem({'organisation': self.organisation})
        other_problem = create_test_problem({'organisation': other_organisation})
        review = create_test_review({'organisation': self.organisation})
        other_review = create_test_review({'organisation': other_organisation})

        # Again create the urls so that we can use them to check what's shown
        problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'choices'})
        other_problem_url = reverse('problem-view', kwargs={'pk': other_problem.id, 'cobrand': 'choices'})
        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        other_review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': other_review.api_posting_id,
                'ods_code': other_review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )

        # Get the page with no filtering to check everything's shown
        resp = self.client.get(self.live_feed_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, other_problem_url)
        self.assertContains(resp, review_url)
        self.assertContains(resp, other_review_url)

        filtered_url_string = "{0}?organisation={1}"

        # Filter to the first org
        filtered_url = filtered_url_string.format(self.live_feed_url, self.organisation.id)
        resp = self.client.get(filtered_url)
        self.assertContains(resp, problem_url)
        self.assertContains(resp, review_url)
        self.assertNotContains(resp, other_problem_url)
        self.assertNotContains(resp, other_review_url)

        # Swap filtering to the other org
        filtered_url = filtered_url_string.format(self.live_feed_url, other_organisation.id)
        resp = self.client.get(filtered_url)
        self.assertContains(resp, other_problem_url)
        self.assertContains(resp, other_review_url)
        self.assertNotContains(resp, problem_url)
        self.assertNotContains(resp, review_url)

    def test_shows_open_and_closed_problems(self):
        open_problem = create_test_problem({'organisation': self.organisation, 'status': Problem.NEW})
        closed_problem = create_test_problem({'organisation': self.organisation, 'status': Problem.RESOLVED})

        open_problem_url = reverse('problem-view', kwargs={'pk': open_problem.id, 'cobrand': 'choices'})
        closed_problem_url = reverse('problem-view', kwargs={'pk': closed_problem.id, 'cobrand': 'choices'})

        resp = self.client.get(self.live_feed_url)

        self.assertContains(resp, open_problem_url)
        self.assertContains(resp, closed_problem_url)

    def test_shows_unmoderated_problems(self):
        unmoderated_problem = create_test_problem({
            'organisation': self.organisation,
            'publication_status': Problem.NOT_MODERATED
        })
        moderated_problem = create_test_problem({
            'organisation': self.organisation,
            'publication_status': Problem.PUBLISHED
        })

        unmoderated_problem_url = reverse('problem-view', kwargs={'pk': unmoderated_problem.id, 'cobrand': 'choices'})
        moderated_problem_url = reverse('problem-view', kwargs={'pk': moderated_problem.id, 'cobrand': 'choices'})

        resp = self.client.get(self.live_feed_url)

        self.assertContains(resp, unmoderated_problem_url)
        self.assertContains(resp, moderated_problem_url)

    def test_doesnt_show_requiring_second_tier_moderation_problems(self):
        second_tier_moderation_problem = create_test_problem({
            'organisation': self.organisation,
            'publication_status': Problem.NOT_MODERATED,
            'requires_second_tier_moderation': True
        })

        second_tier_moderation_problem_url = reverse('problem-view', kwargs={'pk': second_tier_moderation_problem.id, 'cobrand': 'choices'})

        resp = self.client.get(self.live_feed_url)

        self.assertNotContains(resp, second_tier_moderation_problem_url)

    @override_settings(LIVE_FEED_PER_PAGE=2)
    def test_pagination(self):
        # Add three problems
        problem3 = create_test_problem({'organisation': self.organisation})
        problem2 = create_test_problem({'organisation': self.organisation})
        problem1 = create_test_problem({'organisation': self.organisation})

        problem1_url = reverse('problem-view', kwargs={'pk': problem1.id, 'cobrand': 'choices'})
        problem2_url = reverse('problem-view', kwargs={'pk': problem2.id, 'cobrand': 'choices'})
        problem3_url = reverse('problem-view', kwargs={'pk': problem3.id, 'cobrand': 'choices'})

        resp = self.client.get(self.live_feed_url)

        # Check that only two are shown
        self.assertContains(resp, problem1_url)
        self.assertContains(resp, problem2_url)
        self.assertNotContains(resp, problem3_url)

        # Check that there's a pagination setup
        self.assertContains(resp, "?page=2")

        # Go to the first page and check that there's the third problem shown
        resp = self.client.get("{0}?page=2".format(self.live_feed_url))
        self.assertContains(resp, problem3_url)
        self.assertNotContains(resp, problem1_url)
        self.assertNotContains(resp, problem2_url)
        self.assertContains(resp, "?page=1")

    def test_shows_problem_details(self):
        problem = create_test_problem({'organisation': self.organisation})
        problem.status = Problem.RESOLVED
        problem.save()
        resp = self.client.get(self.live_feed_url)
        self.assertEqual(resp.status_code, 200)

        problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'choices'})
        self.assertContains(resp, problem_url)
        self.assertContains(resp, problem.organisation.name)
        self.assertContains(resp, django_date(problem.created, 'd M Y, g:i a'))
        self.assertContains(resp, problem.get_category_display())
        self.assertContains(resp, problem.get_status_display())

    def test_shows_review_details(self):
        review = create_test_review({'organisation': self.organisation})
        resp = self.client.get(self.live_feed_url)
        self.assertEqual(resp.status_code, 200)

        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': review.organisations.all()[0].ods_code,
                'cobrand': 'choices'
            }
        )
        self.assertContains(resp, review_url)
        self.assertContains(resp, review.organisations.all()[0].name)
        self.assertContains(resp, django_date(review.api_published, 'd M Y, g:i a'))
        self.assertContains(resp, capfirst(review.title))
