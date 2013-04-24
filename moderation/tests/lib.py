from django.core.urlresolvers import reverse
from django.test import TransactionTestCase

from organisations.models import Organisation
from organisations.tests.lib import create_test_problem, create_test_organisation, AuthorizationTestCase
from issues.models import Problem

class BaseModerationTestCase(AuthorizationTestCase, TransactionTestCase):

    def setUp(self):
        # Add some issues
        super(BaseModerationTestCase, self).setUp()
        self.test_problem = create_test_problem({'organisation':self.test_organisation})
        self.test_second_tier_moderation_problem = create_test_problem({'organisation': self.test_organisation,
                                                                            'requires_second_tier_moderation': True})
        self.home_url = reverse('moderate-home')
        self.lookup_url = reverse('moderate-lookup')
        self.problem_form_url = reverse('moderate-form', kwargs={'pk':self.test_problem.id})
        self.confirm_url = reverse('moderate-confirm')
        self.second_tier_home_url = reverse('second-tier-moderate-home')
        self.second_tier_problem_form_url = reverse('second-tier-moderate-form', kwargs={'pk':self.test_second_tier_moderation_problem.id})
        self.second_tier_confirm_url = reverse('second-tier-moderate-confirm')
        self.all_case_handler_urls = [self.home_url,
                                     self.lookup_url,
                                     self.problem_form_url,
                                     self.confirm_url]

        self.all_second_tier_moderator_urls = [self.second_tier_home_url,
                                         self.second_tier_problem_form_url,
                                         self.second_tier_confirm_url]
        self.all_urls = self.all_case_handler_urls + self.all_second_tier_moderator_urls

    def assert_expected_publication_status(self, expected_status, form_values, url, problem):
        resp = self.client.post(url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertEqual(problem.publication_status, expected_status)

