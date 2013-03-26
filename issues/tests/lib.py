from django.test import TestCase

import reversion

from organisations.tests.lib import create_test_instance

from ..lib import changed_attrs, changes_as_string, changes_for_model, base32_to_int, int_to_base32, MistypedIDException
from ..models import Problem, Question

class LibTests(TestCase):

    def setUp(self):
        self.old = {'status': Problem.NEW, 'publication_status': Problem.HIDDEN, 'moderated': Problem.NOT_MODERATED}
        self.new = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED, 'moderated': Problem.MODERATED}

        self.old_missing = {'publication_status': Problem.HIDDEN, 'moderated': Problem.NOT_MODERATED}
        self.new_missing = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED}

        self.old_unchanged = {'status': Problem.NEW, 'publication_status': Problem.HIDDEN, 'moderated': Problem.NOT_MODERATED}
        self.new_unchanged = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.HIDDEN, 'moderated': Problem.MODERATED}

    def test_changed_attrs_happy_path(self):
        expected_changed = {
            'status': [Problem.NEW, Problem.ACKNOWLEDGED],
            'publication_status': [Problem.HIDDEN, Problem.PUBLISHED],
            'moderated': [Problem.NOT_MODERATED, Problem.MODERATED]
        }
        actual_changed = changed_attrs(self.old, self.new, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)


    def test_changed_attrs_missing_attrs(self):
        expected_changed = {
            'status': [None, Problem.ACKNOWLEDGED],
            'publication_status': [Problem.HIDDEN, Problem.PUBLISHED],
            'moderated': [Problem.NOT_MODERATED, None]
        }
        actual_changed = changed_attrs(self.old_missing, self.new_missing, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changed_attrs_unchanged_attrs(self):
        expected_changed = {
            'status': [Problem.NEW, Problem.ACKNOWLEDGED],
            'moderated': [Problem.NOT_MODERATED, Problem.MODERATED]
        }
        actual_changed = changed_attrs(self.old_unchanged, self.new_unchanged, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changed_attrs_question_attrs(self):
        expected_changed = {
            'status': [Problem.NEW, Problem.ACKNOWLEDGED],
        }
        actual_changed = changed_attrs(self.old, self.new, Question.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changes_as_string_happy_path(self):
        expected = "Moderated, Published and Acknowledged"
        changes = changed_attrs(self.old, self.new, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_unchanged_attrs(self):
        expected = "Moderated and Acknowledged"
        changes = changed_attrs(self.old_unchanged, self.new_unchanged, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_escalated(self):
        new_escalated = {'status':Problem.ESCALATED, 'publication_status': Problem.HIDDEN, 'moderated': Problem.MODERATED}

        expected = "Moderated and Escalated"
        changes = changed_attrs(self.old, new_escalated, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_question(self):
        old = {'status':Question.NEW}
        new = {'status':Question.RESOLVED}

        expected = "Answered"
        changes = changed_attrs(old, new, Question.REVISION_ATTRS)
        actual = changes_as_string(changes, Question.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_for_model(self):
        # Make a problem and give it some history
        with reversion.create_revision():
            problem = create_test_instance(Problem, {'status': Problem.NEW,
                                                     'moderated': Problem.NOT_MODERATED,
                                                     'publication_status': Problem.HIDDEN})
        problem = Problem.objects.get(pk=problem.id)
        problem.status = Problem.ACKNOWLEDGED
        with reversion.create_revision():
            problem.save()

        problem = Problem.objects.get(pk=problem.id)
        problem.status = Problem.RESOLVED
        with reversion.create_revision():
            problem.save()

        problem = Problem.objects.get(pk=problem.id)
        problem.moderated = Problem.MODERATED
        problem.publication_status = Problem.PUBLISHED
        with reversion.create_revision():
            problem.save()

        expected_changes = [
            {'user': None, 'description': 'Acknowledged'},
            {'user': None, 'description': 'Resolved'},
            {'user': None, 'description': 'Moderated and Published'}
        ]
        actual_changes = changes_for_model(problem)

        self.assertEqual(len(expected_changes), len(actual_changes))
        for index, change in enumerate(actual_changes):
            self.assertEqual(change, expected_changes[index])

    def test_base32_roundtrip_conversion(self):
        self.assertEqual(829384, base32_to_int(int_to_base32(829384)))

    def test_base32_to_int_raises_exception_on_mistyped_characters(self):
        self.assertEqual(373536, base32_to_int('bcs0'))
        with self.assertRaises(MistypedIDException) as context_manager:
            base32_to_int('bcso')
        exception = context_manager.exception
        self.assertEqual(str(exception), '373536')


