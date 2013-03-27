from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question
from responses.models import ProblemResponse

from .lib import BaseModerationTestCase

class LookupFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LookupFormTests, self).setUp()
        self.closed_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                             'status': Problem.RESOLVED})
        self.moderated_problem = create_test_instance(Problem, {'organisation':self.test_organisation,
                                                                'moderated': Problem.MODERATED})
        self.login_as(self.case_handler)

    def test_happy_path(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.test_problem.id)})
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

    def test_form_rejects_questions(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Question.PREFIX, self.test_question.id)})
        self.assertFormError(resp, 'form', None, 'Sorry, that reference number is not recognised')

    def test_form_allows_moderated_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.moderated_problem.id)})
        self.assertRedirects(resp, '/private/moderate/{0}'.format(self.moderated_problem.id))

    def test_form_allows_closed_problems(self):
        resp = self.client.post(self.lookup_url, {'reference_number': '{0}{1}'.format(Problem.PREFIX, self.closed_problem.id)})
        self.assertRedirects(resp, '/private/moderate/{0}'.format(self.closed_problem.id))

class ModerationFormTests(BaseModerationTestCase):

    def setUp(self):
        super(ModerationFormTests, self).setUp()
        self.login_as(self.case_handler)
        self.form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'publish': '',
            'status': self.test_problem.status,
            'moderated': self.test_problem.moderated,
            'commissioned': Problem.NATIONALLY_COMMISSIONED,
            'responses-TOTAL_FORMS': 0,
            'responses-INITIAL_FORMS': 0,
            'responses-MAX_NUM_FORMS': 0,
        }

    def test_moderation_form_sets_moderated(self):
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated, Problem.MODERATED)

    def test_moderation_form_sets_moderated_description(self):
        moderated_description = "{0} moderated".format(self.test_problem.description)
        test_form_values = {
            'moderated_description': moderated_description
        }
        self.form_values.update(test_form_values)
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated_description, moderated_description)

    def test_moderation_form_sets_breach(self):
        test_form_values = {
            'breach': 1
        }
        self.form_values.update(test_form_values)
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.breach, True)

    def test_moderation_form_sets_status(self):
        test_form_values = {
            'status': Problem.ESCALATED
        }
        self.form_values.update(test_form_values)
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.status, Problem.ESCALATED)

    def test_moderation_form_sets_publication_status_to_published_when_publish_clicked(self):
        self.assert_expected_publication_status(Problem.PUBLISHED,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def test_moderation_form_sets_publication_status_to_private_when_keep_private_clicked(self):
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_publication_status(Problem.HIDDEN,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def test_moderation_form_sets_publication_status_to_private_when_requires_legal_moderation_clicked(self):
        test_form_values = {
            'now_requires_legal_moderation': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_publication_status(Problem.HIDDEN,
                                                self.form_values,
                                                self.problem_form_url,
                                                self.test_problem)

    def assert_expected_requires_legal_moderation(self, expected_value, form_values):
        resp = self.client.post(self.problem_form_url, form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.requires_legal_moderation, expected_value)

    def test_form_sets_requires_legal_moderation_when_requires_legal_moderation_clicked(self):
        test_form_values = {
            'now_requires_legal_moderation': '',
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_requires_legal_moderation(True, self.form_values)

    def test_form_unsets_requires_legal_moderation_when_keep_private_clicked(self):
        self.test_problem.requires_legal_moderation = True
        self.test_problem.save()
        test_form_values = {
            'keep_private': '',
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_requires_legal_moderation(False, self.form_values)

    def test_form_unsets_requires_legal_moderation_when_publish_clicked(self):
        self.test_problem.requires_legal_moderation = True
        self.test_problem.save()
        test_form_values = {
            'publish': ''
        }
        self.form_values.update(test_form_values)
        self.assert_expected_requires_legal_moderation(False, self.form_values)

    def test_form_redirects_to_confirm_url(self):
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertRedirects(resp, self.confirm_url)
        resp = self.client.get(self.confirm_url)
        self.assertContains(resp, self.home_url)

    def test_moderation_form_requires_moderated_description_when_publishing_public_problems(self):
        del self.form_values['moderated_description']
        resp = self.client.post(self.problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', 'moderated_description', 'You must moderate a version of the problem details when publishing public problems.')

    def test_moderation_form_doesnt_requires_moderated_description_for_private_problems(self):
        self.test_problem.public = False
        self.test_problem.save()
        expected_status = Problem.PUBLISHED
        del self.form_values['moderated_description']
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_moderation_form_doesnt_require_moderated_description_when_hiding_problems(self):
        expected_status = Problem.HIDDEN
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        del self.form_values['moderated_description']
        resp = self.client.post(self.problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_moderation_form_can_moderate_responses(self):
        # Add some responses to the test problem
        response1 = ProblemResponse.objects.create(response="Response 1", issue=self.test_problem)
        response2 = ProblemResponse.objects.create(response="Response 2", issue=self.test_problem)
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

class LegalModerationFormTests(BaseModerationTestCase):

    def setUp(self):
        super(LegalModerationFormTests, self).setUp()
        self.login_as(self.legal_moderator)
        self.form_values = {
            'publication_status': self.test_legal_moderation_problem.publication_status,
            'moderated_description': self.test_legal_moderation_problem.description,
            'publish': '',
        }

    def test_legal_moderation_form_redirects_to_legal_confirm_url(self):
        resp = self.client.post(self.legal_problem_form_url, self.form_values)
        self.assertRedirects(resp, self.legal_confirm_url)
        resp = self.client.get(self.legal_confirm_url)
        self.assertContains(resp, self.legal_home_url)

    def test_legal_moderation_form_sets_requires_legal_moderation_to_false(self):
        resp = self.client.post(self.legal_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_legal_moderation_problem.id)
        self.assertEqual(problem.requires_legal_moderation, False)

    def test_legal_moderation_form_requires_moderated_description_when_publishing_public_problems(self):
        del self.form_values['moderated_description']
        resp = self.client.post(self.legal_problem_form_url, self.form_values)
        self.assertFormError(resp, 'form', 'moderated_description', 'You must moderate a version of the problem details when publishing public problems.')

    def test_legal_moderation_form_doesnt_require_moderated_description_for_private_problems(self):
        self.test_legal_moderation_problem.public = False
        self.test_legal_moderation_problem.save()
        expected_status = Problem.PUBLISHED
        del self.form_values['moderated_description']
        resp = self.client.post(self.legal_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_legal_moderation_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_legal_moderation_form_doesnt_require_moderated_description_when_hiding_problems(self):
        expected_status = Problem.HIDDEN
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        del self.form_values['moderated_description']
        resp = self.client.post(self.legal_problem_form_url, self.form_values)
        problem = Problem.objects.get(pk=self.test_legal_moderation_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_legal_moderation_form_sets_publication_status_to_published_when_publish_clicked(self):
        self.assert_expected_publication_status(Problem.PUBLISHED,
                                                self.form_values,
                                                self.legal_problem_form_url,
                                                self.test_legal_moderation_problem)

    def test_legal_moderation_form_sets_publication_status_to_private_when_keep_private_clicked(self):
        test_form_values = {
            'keep_private': ''
        }
        self.form_values.update(test_form_values)
        del self.form_values['publish']
        self.assert_expected_publication_status(Problem.HIDDEN,
                                                self.form_values,
                                                self.legal_problem_form_url,
                                                self.test_legal_moderation_problem)
