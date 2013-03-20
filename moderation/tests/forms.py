from django.core.urlresolvers import reverse

from organisations.models import Organisation
from organisations.tests.lib import create_test_instance, create_test_organisation
from issues.models import Problem, Question

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

    def test_moderation_form_sets_moderated(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated, Problem.MODERATED)

    def test_moderation_form_sets_moderated_description(self):
        moderated_description = "{0} moderated".format(self.test_problem.description)
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': moderated_description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.moderated_description, moderated_description)

    def test_moderation_form_sets_breach(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'breach': 1,
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.breach, True)

    def test_moderation_form_sets_status(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': Problem.ESCALATED
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.status, Problem.ESCALATED)

    def assert_expected_publication_status(self, expected_status, form_values):
        resp = self.client.post(self.problem_form_url, form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_form_sets_publication_status_to_published_when_publish_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_publication_status(Problem.PUBLISHED, test_form_values)

    def test_form_sets_publication_status_to_private_when_keep_private_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'keep_private': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_publication_status(Problem.HIDDEN, test_form_values)

    def test_form_sets_publication_status_to_private_when_requires_legal_moderation_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'now_requires_legal_moderation': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_publication_status(Problem.HIDDEN, test_form_values)

    def assert_expected_requires_legal_moderation(self, expected_value, form_values):
        resp = self.client.post(self.problem_form_url, form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.requires_legal_moderation, expected_value)

    def test_form_sets_requires_legal_moderation_when_requires_legal_moderation_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'now_requires_legal_moderation': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_requires_legal_moderation(True, test_form_values)

    def test_form_unsets_requires_legal_moderation_when_keep_private_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'keep_private': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_requires_legal_moderation(False, test_form_values)

    def test_form_unsets_requires_legal_moderation_when_publish_clicked(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        self.assert_expected_requires_legal_moderation(False, test_form_values)

    def test_form_redirects_to_confirm_url(self):
        status = Problem.RESOLVED
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated_description': self.test_problem.description,
            'moderated': self.test_problem.moderated,
            'keep_private': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        self.assertRedirects(resp, reverse('moderate-confirm'))

    def test_moderation_form_requires_moderated_description_when_publishing_public_problems(self):
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        self.assertFormError(resp, 'form', 'moderated_description', 'You must moderate a version of the problem details when publishing public problems.')

    def test_moderation_form_doesnt_requires_moderated_description_for_private_problems(self):
        self.test_problem.public = False
        self.test_problem.save()
        expected_status = Problem.PUBLISHED
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated': self.test_problem.moderated,
            'publish': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)

    def test_moderation_form_doesnt_require_moderated_description_when_hiding_problems(self):
        expected_status = Problem.HIDDEN
        test_form_values = {
            'publication_status': self.test_problem.publication_status,
            'moderated': self.test_problem.moderated,
            'keep_private': '',
            'status': self.test_problem.status,
        }
        resp = self.client.post(self.problem_form_url, test_form_values)
        problem = Problem.objects.get(pk=self.test_problem.id)
        self.assertEqual(problem.publication_status, expected_status)
