from django.test import TestCase
from django.core.urlresolvers import reverse

from issues.models import Problem, MessageModel

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
                                                              'publication_status': MessageModel.PUBLISHED})
        # Create a hidden problem
        self.hidden_problem = create_test_instance(Problem, {'organisation': self.test_organisation,
                                                             'moderated': True,
                                                             'publication_status': MessageModel.HIDDEN})
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
            self.test_allowed_user,
            self.test_other_provider_user,
            self.test_moderator,
            self.superuser, # Django superuser
            self.test_pals_user,
            self.test_no_provider_user
        ]

    def test_superuser_access_logged(self):
        self.login_as(self.test_nhs_superuser)

        for path in self.test_urls:
            resp = self.client.get(path)
            self.assertIsNotNone(SuperuserLogEntry.objects.get(user=self.test_nhs_superuser, path=path))

    def test_other_user_access_not_logged(self):
        for user in self.users_who_should_not_be_logged:

            self.login_as(user)

            for path in self.test_urls:
                # The following might 403 for some users, but it shouldn't affect the logging
                resp = self.client.get(path)
                self.assertEqual(SuperuserLogEntry.objects.all().filter(user=user, path=path).count(), 0)
