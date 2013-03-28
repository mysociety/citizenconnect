from django.test import TestCase
from django.core.urlresolvers import reverse

from issues.models import Problem

from ..models import SuperuserLogEntry
from .lib import AuthorizationTestCase, create_test_instance

class SuperuserLogTests(AuthorizationTestCase):

    def setUp(self):
        super(SuperuserLogTests, self).setUp()
        # Create an unmoderated problem
        self.unmoderated_problem = create_test_instance(Problem, {'organisation': self.test_organisation})
        # Create a private problem
        self.private_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                              'public':False,
                                                              'moderated': True,
                                                              'publication_status': Problem.PUBLISHED})
        # Create a hidden problem
        self.hidden_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                             'moderated': True,
                                                             'publication_status': Problem.HIDDEN})
        self.test_urls = [
            reverse('home', kwargs={'cobrand':'choices'}),
            reverse('private-map'),
            reverse('org-dashboard', kwargs={'ods_code':self.test_organisation.ods_code}),
            reverse('private-org-problems', kwargs={'ods_code':self.test_organisation.ods_code}),
            reverse('problem-view', kwargs={'cobrand':'choices', 'pk':self.unmoderated_problem.id}),
            reverse('problem-view', kwargs={'cobrand':'choices', 'pk':self.private_problem.id}),
            reverse('problem-view', kwargs={'cobrand':'choices', 'pk':self.hidden_problem.id})
        ]
        self.users_who_should_not_be_logged = [
            self.provider,
            self.other_provider,
            self.ccg_user,
            self.other_ccg_user,
            self.case_handler,
            self.superuser, # Django superuser
            self.pals,
            self.no_provider
        ]

    def test_superuser_access_logged(self):
        self.login_as(self.nhs_superuser)

        for path in self.test_urls:
            resp = self.client.get(path)
            self.assertIsNotNone(SuperuserLogEntry.objects.get(user=self.nhs_superuser, path=path))

    def test_other_user_access_not_logged(self):
        for user in self.users_who_should_not_be_logged:

            self.login_as(user)

            for path in self.test_urls:
                # The following might 403 for some users, but it shouldn't affect the logging
                resp = self.client.get(path)
                self.assertEqual(SuperuserLogEntry.objects.all().filter(user=user, path=path).count(), 0)

class SuperuserLogViewTests(AuthorizationTestCase):

    def setUp(self):
        super(SuperuserLogViewTests, self).setUp()
        self.login_as(self.nhs_superuser)
        self.logs_url = reverse('private-map')

    def test_log_page_exists(self):
        resp = self.client.get(reverse('superuser-logs'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Superuser Logs")

    def test_log_page_shows_logs(self):
        # Go to a page so that it'll be logged
        map_url = self.logs_url
        self.client.get(map_url)

        resp = self.client.get(reverse('superuser-logs'))

        log_entry = SuperuserLogEntry.objects.get(user=self.nhs_superuser, path=map_url)

        self.assertTrue(log_entry in resp.context['logs'])
        self.assertContains(resp, self.nhs_superuser.username)
        self.assertContains(resp, map_url)

    def test_log_page_only_accessible_to_superusers(self):
        non_superusers = [
            self.provider,
            self.other_provider,
            self.case_handler,
            self.pals,
            self.no_provider
        ]

        for user in non_superusers:
            self.login_as(user)
            resp = self.client.get(self.logs_url)
            self.assertEqual(resp.status_code, 403)
