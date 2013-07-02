import os
import tempfile
import shutil

from django.core.urlresolvers import reverse
from django.core.files.images import ImageFile
from django.conf import settings
from django.test.utils import override_settings

from sorl.thumbnail import get_thumbnail

from organisations.tests.lib import create_test_problem
from issues.models import Problem, ProblemImage
from responses.models import ProblemResponse

from .lib import BaseModerationTestCase


class BasicViewTests(BaseModerationTestCase):

    def setUp(self):
        super(BasicViewTests, self).setUp()
        self.login_as(self.case_handler)

    def test_views_exist(self):
        for url in self.all_case_handler_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_views_require_login(self):
        self.client.logout()

        for url in self.all_urls:
            expected_login_url = "{0}?next={1}".format(self.login_url, url)
            resp = self.client.get(url)
            self.assertRedirects(resp, expected_login_url)

    def test_views_inacessible_to_providers(self):
        self.client.logout()
        self.login_as(self.trust_user)

        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_views_inacessible_to_ccgs(self):
        self.client.logout()
        self.login_as(self.ccg_user)

        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)

    def test_views_accessible_to_superusers(self):
        for user in self.users_who_can_access_everything:
            self.login_as(user)
            for url in self.all_urls:
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200)

    def test_views_accessible_to_second_tier_moderators(self):
        self.client.logout()
        self.login_as(self.second_tier_moderator)
        for url in self.all_second_tier_moderator_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)

    def test_views_inaccessible_to_customer_contact_centre(self):
        self.client.logout()
        self.login_as(self.customer_contact_centre_user)
        for url in self.all_urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 403)


class HomeViewTests(BaseModerationTestCase):

    def setUp(self):
        super(HomeViewTests, self).setUp()

        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'status': Problem.RESOLVED})
        self.moderated_problem = create_test_problem({'organisation': self.test_hospital,
                                                      'publication_status': Problem.PUBLISHED})

        self.login_as(self.case_handler)

    def test_issues_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.test_problem in resp.context['issues'])
        self.assertTrue(self.closed_problem in resp.context['issues'])

    def test_moderated_issues_not_in_context(self):
        resp = self.client.get(self.home_url)
        self.assertTrue(self.moderated_problem not in resp.context['issues'])

    def test_issues_displayed(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.test_problem.private_summary)
        self.assertContains(resp, self.closed_problem.private_summary)

    def test_issues_link_to_moderate_form(self):
        resp = self.client.get(self.home_url)
        self.assertContains(resp, self.problem_form_url)

    def test_high_priority_problems_identified(self):
        expected = 'problem-table__highlight'

        # Test without there being a priority entry
        resp = self.client.get(self.home_url)
        self.assertNotContains(resp, expected)

        # add high priority entry
        create_test_problem(
            {
                'organisation': self.test_hospital,
                'priority': Problem.PRIORITY_HIGH
            }
        )

        # check it is now listed
        resp = self.client.get(self.home_url)
        self.assertContains(resp, expected)


class SecondTierModerationHomeViewTests(BaseModerationTestCase):

    def setUp(self):
        super(SecondTierModerationHomeViewTests, self).setUp()
        self.second_tier_moderation = create_test_problem({'organisation': self.test_hospital,
                                                           'requires_second_tier_moderation': True})
        self.no_second_tier_moderation = create_test_problem({'organisation': self.test_hospital})
        self.login_as(self.second_tier_moderator)

    def test_issues_in_context(self):
        resp = self.client.get(self.second_tier_home_url)
        self.assertTrue(self.second_tier_moderation in resp.context['issues'])

    def test_issues_not_requiring_second_tier_moderation_not_in_context(self):
        resp = self.client.get(self.second_tier_home_url)
        self.assertTrue(self.no_second_tier_moderation not in resp.context['issues'])

    def test_issues_link_to_second_tier_moderate_form(self):
        resp = self.client.get(self.second_tier_home_url)
        self.second_tier_problem_form_url = reverse('second-tier-moderate-form',
                                                    kwargs={'pk': self.second_tier_moderation.id})
        self.assertContains(resp, self.second_tier_problem_form_url)

    def test_inaccessible_to_case_handlers(self):
        self.client.logout()
        self.login_as(self.case_handler)
        resp = self.client.get(self.second_tier_home_url)
        self.assertEqual(resp.status_code, 403)

    def test_high_priority_problems_identified(self):
        expected = 'problem-table__highlight'

        # Test without there being a priority entry
        resp = self.client.get(self.second_tier_home_url)
        self.assertNotContains(resp, expected)

        # add high priority entry
        self.second_tier_moderation.priority = Problem.PRIORITY_HIGH
        self.second_tier_moderation.save()

        # check it is now highlighted
        resp = self.client.get(self.second_tier_home_url)
        self.assertContains(resp, expected)

    def test_breach_problems_identified(self):
        expected = '<div class="problem-table__flag__breach">b</div>'

        # Test without there being a breach entry
        resp = self.client.get(self.second_tier_home_url)
        self.assertNotContains(resp, expected)

        # add breach entry
        self.second_tier_moderation.breach = True
        self.second_tier_moderation.save()

        # check it is now listed
        resp = self.client.get(self.second_tier_home_url)
        self.assertContains(resp, expected)

    def test_escalated_problems_identified(self):
        expected = '<div class="problem-table__flag__escalate">e</div>'

        # Test without there being an escalated enry
        resp = self.client.get(self.second_tier_home_url)
        self.assertNotContains(resp, expected)

        # add an escalated entry
        self.second_tier_moderation.status = Problem.ESCALATED_ACKNOWLEDGED
        self.second_tier_moderation.save()

        # check it is now listed
        resp = self.client.get(self.second_tier_home_url)
        self.assertContains(resp, expected)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ModerateFormViewTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerateFormViewTests, self).setUp()

        self.closed_problem = create_test_problem({'organisation': self.test_hospital,
                                                   'status': Problem.RESOLVED})
        self.moderated_problem = create_test_problem({'organisation': self.test_hospital,
                                                      'publication_status': Problem.PUBLISHED})

        self.login_as(self.case_handler)

    def tearDown(self):
        # Clear the images folder
        images_folder = os.path.join(settings.MEDIA_ROOT, 'images')
        if(os.path.exists(images_folder)):
            shutil.rmtree(images_folder)

    def test_problem_in_context(self):
        resp = self.client.get(self.problem_form_url)
        self.assertEqual(resp.context['issue'], self.test_problem)

    def test_issue_data_displayed(self):
        # Add some responses to the issue too
        response1 = ProblemResponse.objects.create(response="response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="response 2", issue=self.test_problem)

        resp = self.client.get(self.problem_form_url)
        self.assertContains(resp, self.test_problem.reference_number)
        self.assertContains(resp, self.test_problem.reporter_name)
        self.assertContains(resp, self.test_problem.description)
        self.assertContains(resp, self.test_problem.organisation.name)
        self.assertContains(resp, response1.response)
        self.assertContains(resp, response2.response)

    def test_problem_images_displayed(self):
        # Add some problem images
        fixtures_dir = os.path.join(settings.PROJECT_ROOT, 'issues', 'tests', 'fixtures')
        test_image = ImageFile(open(os.path.join(fixtures_dir, 'test.jpg')))
        image1 = ProblemImage.objects.create(problem=self.test_problem, image=test_image)
        image2 = ProblemImage.objects.create(problem=self.test_problem, image=test_image)
        expected_thumbnail1 = get_thumbnail(image1.image, '150')
        expected_thumbnail2 = get_thumbnail(image2.image, '150')
        expected_image_tag = '<img src="{0}"'

        resp = self.client.get(self.problem_form_url)
        self.assertContains(resp, '<p class="info">There are <strong>2</strong> images associated with this problem report.</p>')
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail1.url))
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail2.url))

    def test_moderated_issues_accepted(self):
        resp = self.client.get(reverse('moderate-form', kwargs={'pk': self.moderated_problem.id}))
        self.assertEqual(resp.status_code, 200)

    def test_closed_issues_accepted(self):
        resp = self.client.get(reverse('moderate-form', kwargs={'pk': self.closed_problem.id}))
        self.assertEqual(resp.status_code, 200)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SecondTierModerateFormViewTests(BaseModerationTestCase):

    def setUp(self):
        super(SecondTierModerateFormViewTests, self).setUp()
        self.login_as(self.second_tier_moderator)

    def tearDown(self):
        # Clear the images folder
        images_folder = os.path.join(settings.MEDIA_ROOT, 'images')
        if(os.path.exists(images_folder)):
            shutil.rmtree(images_folder)

    def test_problem_in_context(self):
        resp = self.client.get(self.second_tier_problem_form_url)
        self.assertEqual(resp.context['issue'], self.test_second_tier_moderation_problem)

    def test_issues_not_requiring_second_tier_moderation_rejected(self):
        second_tier_moderation_form_url = reverse('second-tier-moderate-form',
                                                  kwargs={'pk': self.test_problem.id})
        resp = self.client.get(second_tier_moderation_form_url)
        self.assertEqual(resp.status_code, 404)

    def test_problem_images_displayed(self):
        # Add some problem images
        fixtures_dir = os.path.join(settings.PROJECT_ROOT, 'issues', 'tests', 'fixtures')
        test_image = ImageFile(open(os.path.join(fixtures_dir, 'test.jpg')))
        image1 = ProblemImage.objects.create(problem=self.test_second_tier_moderation_problem, image=test_image)
        image2 = ProblemImage.objects.create(problem=self.test_second_tier_moderation_problem, image=test_image)
        expected_thumbnail1 = get_thumbnail(image1.image, '150')
        expected_thumbnail2 = get_thumbnail(image2.image, '150')
        expected_image_tag = '<img src="{0}"'

        resp = self.client.get(self.second_tier_problem_form_url)
        self.assertContains(resp, '<p class="info">There are <strong>2</strong> images associated with this problem report.</p>')
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail1.url))
        self.assertContains(resp, expected_image_tag.format(expected_thumbnail2.url))
