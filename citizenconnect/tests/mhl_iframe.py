from django.test import TestCase

from django.core.urlresolvers import reverse

from organisations.tests.lib import (
    create_test_organisation,
    create_test_problem
)

from issues.models import Problem

from reviews_display.tests import create_test_review


class MHLIframeTests(TestCase):

    def setUp(self):
        self.iframe_url = reverse('mhl-iframe')

    def test_doesnt_include_nav(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<ul class="site-nav">')

    def test_doesnt_include_mhl_header(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div id="myhealthlondon-header"')

    def test_doesnt_include_footer(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div class="footer">')

    def test_doesnt_include_mhl_footer(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div id="myhealthlondon-footer">')

    def test_includes_cta_buttons_with_target_blank(self):
        reviews_url = reverse('reviews-pick-provider', kwargs={'cobrand': 'myhealthlondon'})
        expected_reviews_cta = '<a target="_blank" href="{0}"'.format(reviews_url)

        expected_questions_cta = '<a target="_blank" href="https://www.nhsdirect.nhs.uk/CheckSymptoms/HealthEnquiry.aspx"'

        problems_url = reverse('problems-pick-provider', kwargs={'cobrand': 'myhealthlondon'})
        expected_problems_cta = '<a target="_blank" href="{0}"'.format(problems_url)

        resp = self.client.get(self.iframe_url)

        self.assertContains(resp, expected_reviews_cta)
        self.assertContains(resp, expected_questions_cta)
        self.assertContains(resp, expected_problems_cta)

    def test_includes_common_questions_link_with_target_blank(self):
        common_questions_url = reverse('common-questions', kwargs={'cobrand': 'myhealthlondon'})
        expected_questions_link = '<a target="_blank" href="{0}"'.format(common_questions_url)
        resp = self.client.get(self.iframe_url)
        self.assertContains(resp, expected_questions_link)

    def test_includes_latest_feed_with_target_blank(self):
        # Add a problem and a review
        organisation = create_test_organisation({})
        problem = create_test_problem({
            'organisation': organisation,
            'publication_status': Problem.PUBLISHED
        })
        review = create_test_review({'organisation': organisation})

        problem_url = reverse('problem-view', kwargs={'pk': problem.id, 'cobrand': 'myhealthlondon'})
        expected_problem_link = '<a target="_blank" href="{0}"'.format(problem_url)

        review_url = reverse(
            'review-detail',
            kwargs={
                'api_posting_id': review.api_posting_id,
                'ods_code': organisation.ods_code,
                'cobrand': 'myhealthlondon'
            }
        )
        expected_review_link = '<a target="_blank" href="{0}">'.format(review_url)

        resp = self.client.get(self.iframe_url)

        self.assertContains(resp, expected_review_link)
        self.assertContains(resp, expected_problem_link)
