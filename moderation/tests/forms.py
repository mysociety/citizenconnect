from organisations.models import Organisation
from organisations.tests.lib import create_test_problem
from issues.models import Problem
from responses.models import ProblemResponse

from .lib import BaseModerationTestCase

from django.core.urlresolvers import reverse


class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_problem(
            {
                'organisation': self.test_hospital,
                'status': Problem.RESOLVED
            }
        )
        self.moderated_problem = create_test_problem(
            {
                'organisation': self.test_hospital,
                'publication_status': Problem.PUBLISHED
            }
        )
        self.login_as(self.case_handler)

    def test_happy_path(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)})
        self.assertRedirects(resp, self.problem_form_url)

    def test_obvious_correction(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX.lower(), self.test_problem.id)})
        self.assertRedirects(resp, self.problem_form_url)

    def test_form_rejects_empty_submissions(self):
        resp = self.client.post(self.lookup_url, {})
        self.assertFormError(resp, 'form', 'reference_number', 'This field is required.')

    def test_form_rejects_unknown_prefixes(self):
        resp = self.client.post(self.lookup_url, {'reference_number': 'a123'})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_rejects_unknown_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}12300'.format(Problem.PREFIX)})
        self.assertFormError(resp, 'form', None, 'Sorry, there are no problems with that reference number')

    def test_form_allows_moderated_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.moderated_problem.id)})
        moderation_url = reverse('moderate-form', kwargs={'pk': self.moderated_problem.id})
        self.assertRedirects(resp, moderation_url)

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        moderation_url = reverse('moderate-form', kwargs={'pk': self.closed_problem.id})
        self.assertRedirects(resp, moderation_url)


class ModerationFormPublicReporterNameMixin(object):

    def setUp(self):
        super(ModerationFormPublicReporterNameMixin, self).setUp()

        self.public_name_problem = create_test_problem({
            'organisation':self.test_hospital,
            'public_reporter_name': True,
            'requires_second_tier_moderation': True,
        })

        self.private_name_problem = create_test_problem({
            'organisation':self.test_hospital,
            'public_reporter_name': False,
            'requires_second_tier_moderation': True,
        })

    def test_public_name_can_be_redacted(self):
        problem = self.public_name_problem
        form_url = reverse(self.form_url_name, kwargs={'pk':problem.id})
        form_values = self.form_values

        # check that the control is there
        resp = self.client.get(form_url)
        self.assertContains(resp, "Publish this name")
        self.assertNotContains(resp, "name is not public, so no need to consider redacting")

        # Leave form checked
        form_values.update({'public_reporter_name': True})
        self.client.get(form_url)
        self.client.post(form_url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertTrue(problem.public_reporter_name)

        # update problem to requires_second_tier_moderation = True
        problem.requires_second_tier_moderation=True
        problem.save()

        # uncheck the form
        form_values.update({'public_reporter_name': False})
        self.client.get(form_url)
        self.client.post(form_url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertFalse(problem.public_reporter_name)

    def test_private_name_can_not_be_redacted(self):
        problem = self.private_name_problem
        form_url = reverse(self.form_url_name, kwargs={'pk':problem.id})
        form_values = self.form_values

        # check that the control is not there
        resp = self.client.get(form_url)
        self.assertNotContains(resp, "Publish this name")
        self.assertContains(resp, "name is not public, so no need to consider redacting")

        # Leave form checked
        form_values.update({'public_reporter_name': True})
        self.client.get(form_url)
        self.client.post(form_url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertFalse(problem.public_reporter_name)

        # update problem to requires_second_tier_moderation = True
        problem.requires_second_tier_moderation=True
        problem.save()

        # uncheck the form
        form_values.update({'public_reporter_name': False})
        self.client.get(form_url)
        self.client.post(form_url, form_values)
        problem = Problem.objects.get(pk=problem.id)
        self.assertFalse(problem.public_reporter_name)


class ModerationFormTests(ModerationFormPublicReporterNameMixin, BaseModerationTestCase):

    form_url_name = 'moderate-form'

    def setUp(self):
        super(ModerationFormTests, self).setUp()
        self.login_as(self.case_handler)
        self.form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'publish': '',
            'status': self.test_problem.status,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'responses-TOTAL_FORMS': 0,
            'responses-INITIAL_FORMS': 0,
            'responses-MAX_NUM_FORMS': 0,
        }
        # Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)

    def test_moderation_form_sets_moderated_description(self):
        moderated_description = "{0} moderated".format(self.test_problem.description)
        test_form_values = {
            'moderated_description': moderated_description
        }
        self.form_values.update(test_form_values)
        self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated_description, moderated_description)

    def test_moderation_form_sets_breach(self):
        test_form_values = {
            'breach': 1
        }
        self.form_values.update(test_form_values)
        self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.breach, True)

    def test_moderation_form_will_not_set_escalated_status(self):
        test_form_values = {
            'status': Problem.ESCALATED
        }
        self.form_values.update(test_form_values)
        self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.status, Problem.NEW)

    def test_moderation_form_sets_status(self):
        test_form_values = {
            'status': Problem.REFERRED_TO_OTHER_PROVIDER
        }
        self.form_values.update(test_form_values)
        self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.status, Problem.REFERRED_TO_OTHER_PROVIDER)

    def test_moderation_form_sets_publication_status_to_published_when_publish_clicked(self):
        self.assert_expected_publication_status(Problem.PUBLISHED,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def test_moderation_form_sets_publication_status_to_not_moderated_when_requires_second_tier_moderation_clicked(self):

        # Change the problem to PUBLISHED so we can test that a change occurs.
        self.test_problem.publication_status = Problem.PUBLISHED
        self.test_problem.save()
        self.client.get(self.problem_form_url)  # deal with versioning

        # change the submit button that'll be used
        self.form_values['now_requires_second_tier_moderation'] = ''
        del self.form_values['publish']

        self.assert_expected_publication_status(Problem.NOT_MODERATED,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def test_moderation_form_sets_publication_status_to_published_when_keep_private_clicked(self):
        # change the submit button that'll be used
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']

        self.assert_expected_publication_status(Problem.PUBLISHED,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def test_moderation_form_sets_public_to_false_when_keep_private_clicked(self):
        # Make sure the problem is public
        self.test_problem.public = True
        self.test_problem.save()
        self.client.get(self.problem_form_url)  # deal with versioning

        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']

        self.client.post(self.problem_form_url, self.form_values)

        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertFalse(problem.public)

    def test_moderation_form_doesnt_allow_setting_of_public_otherwise(self):
        # Make sure the problem is not public
        self.test_problem.public = False
        self.test_problem.save()
        self.client.get(self.problem_form_url)  # deal with versioning

        test_form_values = {
            'public': True
        }
        self.form_values.update(test_form_values)

        self.client.post(self.problem_form_url, self.form_values)

        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertFalse(problem.public)

    def assert_expected_requires_second_tier_moderation(self, expected_value, form_values):
        resp = self.client.post(self.problem_form_url, form_values)
        self.assertEqual(resp.status_code, 302)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.requires_second_tier_moderation, expected_value)

    def test_form_sets_requires_second_tier_moderation_when_requires_second_tier_moderation_clicked(self):
        test_form_values = {
            'now_requires_second_tier_moderation': '',
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_requires_second_tier_moderation(True, self.form_values)

    def test_form_unsets_requires_second_tier_moderation_when_keep_private_clicked(self):
        self.test_problem.requires_second_tier_moderation = True
        self.test_problem.save()
        # Re-Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)
        test_form_values = {
            'keep_private': '',
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_requires_second_tier_moderation(False, self.form_values)

    def test_form_unsets_requires_second_tier_moderation_when_publish_clicked(self):
        self.test_problem.requires_second_tier_moderation = True
        self.test_problem.save()
        # Re-Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)
        test_form_values = {
            'publish': ''
        }
        self.form_values.update(test_form_values)
        self.assert_expected_requires_second_tier_moderation(False, self.form_values)

    def test_form_redirects_to_confirm_url(self):
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertRedirects(resp, self.confirm_url)
        resp = self.client.get(self.confirm_url)
        self.assertContains(resp, self.home_url)

    def test_moderation_form_requires_moderated_description_when_publishing_public_problems(self):
        del self.form_values['moderated_description']
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', 'moderated_description', 'You must moderate a version of the problem details when publishing public problems.')

    def test_moderation_form_doesnt_require_moderated_description_for_private_problems(self):
        # make the problem private
        self.test_problem.public = False
        self.test_problem.save()

        # Re-Get the form as the client to set the initial session vars
        resp = self.client.get(self.problem_form_url)

        # test that the no moderated description message is shown
        self.assertContains(resp, "no need for a moderated description")

        # check that posting a moderated_description is ignored
        self.form_values['moderated_description'] = 'this should be ignored'
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated_description, '')
        self.assertEqual(problem.publication_status, Problem.PUBLISHED)

        # submit again, but without the moderated_description field
        del self.form_values['moderated_description']
        resp = self.client.get(self.problem_form_url)
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated_description, '')
        self.assertEqual(problem.publication_status, Problem.PUBLISHED)

    def test_moderation_form_doesnt_require_moderated_description_when_hiding_problems(self):
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        del self.form_values['moderated_description']

        self.client.post(self.problem_form_url, self.form_values)

        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertFalse(problem.public)

    def test_moderation_form_can_moderate_responses(self):
        # Add some responses to the test problem
        response1 = ProblemResponse.objects.create(response="Response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="Response 2", issue=self.test_problem)
        # Re-Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)
        test_form_values = {
            'responses-TOTAL_FORMS': 2,
            'responses-INITIAL_FORMS': 2,
            'responses-MAX_NUM_FORMS': 0,
            'responses-0-id': response1.id,
            'responses-0-response': "Updated response",
            'responses-0-DELETE': False,
            'responses-1-id': response2.id,
            'responses-1-response': "Response 2",
            'responses-1-DELETE': False
        }
        self.form_values.update(test_form_values)
        resp = self.client.post(self.problem_form_url, self.form_values)
        response1 = ProblemResponse.objects.get(pk=response1.id)
        self.assertEqual(response1.response, "Updated response")

    def test_moderation_form_can_delete_responses(self):
        response1 = ProblemResponse.objects.create(response="Response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="Response 2", issue=self.test_problem)
        # Re-Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)
        test_form_values = {
            'responses-TOTAL_FORMS': 2,
            'responses-INITIAL_FORMS': 2,
            'responses-MAX_NUM_FORMS': 0,
            'responses-0-id': response1.id,
            'responses-0-response': "Updated response",
            'responses-0-DELETE': True,
            'responses-1-id': response2.id,
            'responses-1-response': "Response 2",
            'responses-1-DELETE': False
        }
        self.form_values.update(test_form_values)
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.responses.all().count(), 1)
        self.assertEqual(problem.responses.all()[0], response2)

    def test_moderation_form_requires_commissioned(self):
        del self.form_values['commissioned']
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', 'commissioned', 'This field is required.')

    def test_moderation_form_sets_commissioned(self):
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.commissioned, Problem.NATIONALLY_COMMISSIONED)

class ModerationFormConcurrencyTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerationFormConcurrencyTests, self).setUp()
        self.login_as(self.case_handler)
        self.form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'publish': '',
            'status': self.test_problem.status,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'responses-TOTAL_FORMS': 0,
            'responses-INITIAL_FORMS': 0,
            'responses-MAX_NUM_FORMS': 0,
        }
        # Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)

    def test_initial_versions_set_when_form_loads(self):
        problem_session_version = self.client.session['object_versions'][self.test_problem.id]
        self.assertEqual(problem_session_version, self.test_problem.version)

    def test_version_cleared_when_form_valid(self):
        self.assertTrue(self.test_problem.id in self.client.session['object_versions'])
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFalse(self.test_problem.id in self.client.session['object_versions'])

    def test_form_checks_problem_versions(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.test_problem.id] -= 3000
        session.save()

        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', None, 'Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')

    def test_form_checks_problem_versions_with_responses(self):
        # Add some responses
        response1 = ProblemResponse.objects.create(response="Response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="Response 2", issue=self.test_problem)

        # Re-Get the form as the client to set the initial session vars
        self.client.get(self.problem_form_url)

        # Prep test values
        test_form_values = {
            'responses-TOTAL_FORMS': 2,
            'responses-INITIAL_FORMS': 2,
            'responses-MAX_NUM_FORMS': 0,
            'responses-0-id': response1.id,
            'responses-0-response': response1.response,
            'responses-0-DELETE': False,
            'responses-1-id': response2.id,
            'responses-1-response': response2.response,
            'responses-1-DELETE': False
        }
        self.form_values.update(test_form_values)

        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.test_problem.id] -= 3000
        session.save()

        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', None, 'Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')

    def test_form_resets_version_if_versions_dont_match(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.test_problem.id] -= 3000
        session.save()

        resp = self.client.post(self.problem_form_url, self.form_values)
        session_version = self.client.session['object_versions'][self.test_problem.id]
        self.assertEqual(session_version, self.test_problem.version)


class SecondTierModerationFormTests(ModerationFormPublicReporterNameMixin, BaseModerationTestCase):

    form_url_name = 'second-tier-moderate-form'

    def setUp(self):
        super(SecondTierModerationFormTests, self).setUp()
        self.login_as(self.second_tier_moderator)
        self.form_values = {
            'publication_status': self.test_second_tier_moderation_problem.publication_status,
            'moderated_description': self.test_second_tier_moderation_problem.description,
            'publish': '',
        }
        # Get the form as the client to set the initial session vars
        self.client.get(self.second_tier_problem_form_url)

    def test_second_tier_moderation_form_redirects_to_second_tier_confirm_url(self):
        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        self.assertRedirects(resp, self.second_tier_confirm_url)
        resp = self.client.get(self.second_tier_confirm_url)
        self.assertContains(resp, self.second_tier_home_url)

    def test_second_tier_moderation_form_sets_requires_second_tier_moderation_to_false(self):
        self.client.post(self.second_tier_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertEqual(problem.requires_second_tier_moderation, False)

    def test_second_tier_moderation_form_requires_moderated_description_when_publishing_public_problems(self):
        del self.form_values['moderated_description']
        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', 'moderated_description', 'You must moderate a version of the problem details when publishing public problems.')

    def test_second_tier_moderation_form_doesnt_require_moderated_description_for_private_problems(self):
        self.test_second_tier_moderation_problem.public = False
        self.test_second_tier_moderation_problem.save()

        # Re-get the form as the client to get the latest version into the session
        resp = self.client.get(self.second_tier_problem_form_url)

        # test that the no moderated description message is shown
        self.assertContains(resp, "no need for a moderated description")

        # check that posting a moderated_description is ignored
        self.form_values['moderated_description'] = 'this should be ignored'
        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertEqual(problem.moderated_description, '')
        self.assertEqual(problem.publication_status, Problem.PUBLISHED)

        expected_status = Problem.PUBLISHED
        del self.form_values['moderated_description']
        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_second_tier_moderation_form_doesnt_require_moderated_description_when_hiding_problems(self):
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        del self.form_values['moderated_description']
        self.client.post(self.second_tier_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertFalse(problem.public)

    def test_second_tier_moderation_form_sets_publication_status_to_published_when_publish_clicked(self):
        self.assert_expected_publication_status(Problem.PUBLISHED,
                                                self.form_values,
                                                self.second_tier_problem_form_url,
                                                self.test_second_tier_moderation_problem)

    def test_second_tier_moderation_form_sets_public_to_false_when_keep_private_clicked(self):
        # Make sure the problem is public
        self.test_second_tier_moderation_problem.public = True
        self.test_second_tier_moderation_problem.save()
        self.client.get(self.second_tier_problem_form_url)

        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']

        self.client.post(self.second_tier_problem_form_url, self.form_values)

        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertFalse(problem.public)

    def test_second_tier_moderation_form_doesnt_allow_setting_of_public_otherwise(self):
        # Make sure the problem is not public
        self.test_second_tier_moderation_problem.public = False
        self.test_second_tier_moderation_problem.save()
        self.client.get(self.second_tier_problem_form_url)  # deal with versioning

        test_form_values = {
            'public': True
        }
        self.form_values.update(test_form_values)

        self.client.post(self.second_tier_problem_form_url, self.form_values)

        problem = Problem.objects.get(pk=self.test_second_tier_moderation_problem.id)
        self.assertFalse(problem.public)


class SecondTierModerationFormConcurrencyTests(BaseModerationTestCase):

    def setUp(self):
        super(SecondTierModerationFormConcurrencyTests, self).setUp()
        self.login_as(self.second_tier_moderator)
        self.form_values = {
            'publication_status': self.test_second_tier_moderation_problem.publication_status,
            'moderated_description': self.test_second_tier_moderation_problem.description,
            'publish': '',
        }
        # Get the form as the client to set the initial session vars
        self.client.get(self.second_tier_problem_form_url)

    def test_initial_versions_set_when_form_loads(self):
        problem_session_version = self.client.session['object_versions'][self.test_second_tier_moderation_problem.id]
        self.assertEqual(problem_session_version, self.test_second_tier_moderation_problem.version)

    def test_version_cleared_when_form_valid(self):
        self.assertTrue(self.test_second_tier_moderation_problem.id in self.client.session['object_versions'])
        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        self.assertFalse(self.test_second_tier_moderation_problem.id in self.client.session['object_versions'])

    def test_form_checks_problem_versions(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.test_second_tier_moderation_problem.id] -= 3000
        session.save()

        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', None, 'Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')

    def test_form_resets_version_if_versions_dont_match(self):
        # Tweak the client session so that its' version for the problem is out of date
        session = self.client.session
        session['object_versions'][self.test_second_tier_moderation_problem.id] -= 3000
        session.save()

        resp = self.client.post(self.second_tier_problem_form_url, self.form_values)
        session_version = self.client.session['object_versions'][self.test_second_tier_moderation_problem.id]
        self.assertEqual(session_version, self.test_second_tier_moderation_problem.version)
