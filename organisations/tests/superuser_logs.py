from django.core.urlresolvers import reverse

from issues.models import Problem

from ..models import SuperuserLogEntry
from .lib import AuthorizationTestCase, create_test_problem


class SuperuserLogTests(AuthorizationTestCase):

    def setUp(self):
        super(SuperuserLogTests, self).setUp()
        # Create an unmoderated problem
        self.unmoderated_problem = create_test_problem({'organisation': self.test_organisation})
        # Create a private problem
        self.private_problem = create_test_problem({'organisation': self.test_organisation,
                                                    'public': False,
                                                    'moderated': True,
                                                    'publication_status': Problem.PUBLISHED})
        # Create a hidden problem
        self.hidden_problem = create_test_problem({'organisation': self.test_organisation,
                                                   'moderated': True,
                                                   'publication_status': Problem.HIDDEN})
        self.test_urls = [
            reverse('home', kwargs={'cobrand': 'choices'}),
            reverse('trust-dashboard', kwargs={'code': self.test_organisation.trust.code}),
            reverse('private-org-problems', kwargs={'ods_code': self.test_organisation.ods_code}),
            reverse('problem-view', kwargs={'cobrand': 'choices', 'pk': self.unmoderated_problem.id}),
            reverse('problem-view', kwargs={'cobrand': 'choices', 'pk': self.private_problem.id}),
            reverse('problem-view', kwargs={'cobrand': 'choices', 'pk': self.hidden_problem.id})
        ]
        self.users_who_should_not_be_logged = [
            self.trust_user,
            self.other_provider,
            self.ccg_user,
            self.other_ccg_user,
            self.case_handler,
            self.superuser,  # Django superuser
            self.no_trust_user
        ]

    def test_superuser_access_logged(self):
        self.login_as(self.nhs_superuser)

        for path in self.test_urls:
            self.client.get(path)
            self.assertIsNotNone(SuperuserLogEntry.objects.get(user=self.nhs_superuser, path=path))

    def test_other_user_access_not_logged(self):
        for user in self.users_who_should_not_be_logged:

            self.login_as(user)

            for path in self.test_urls:
                # The following might 403 for some users, but it shouldn't affect the logging
                self.client.get(path)
                self.assertEqual(SuperuserLogEntry.objects.all().filter(user=user, path=path).count(), 0)


class SuperuserLogViewTests(AuthorizationTestCase):

    def setUp(self):
        super(SuperuserLogViewTests, self).setUp()
        self.login_as(self.nhs_superuser)
        self.logs_url = reverse('private-org-problems',
                                kwargs={'ods_code': self.test_organisation.ods_code})

    def test_log_page_exists(self):
        resp = self.client.get(reverse('superuser-logs'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Superuser Logs")

    def test_log_page_shows_logs(self):
        # Go to a page so that it'll be logged
        problems_url = self.logs_url
        self.client.get(problems_url)

        resp = self.client.get(reverse('superuser-logs'))

        log_entry = SuperuserLogEntry.objects.get(user=self.nhs_superuser, path=problems_url)

        self.assertTrue(log_entry in resp.context['logs'])
        self.assertContains(resp, self.nhs_superuser.username)
        self.assertContains(resp, problems_url)

    def test_log_page_only_accessible_to_superusers(self):
        non_superusers = [
            self.trust_user,
            self.other_provider,
            self.case_handler,
            self.no_trust_user
        ]

        for user in non_superusers:
            self.login_as(user)
            resp = self.client.get(reverse('superuser-logs'))
            self.assertEqual(resp.status_code, 403)
