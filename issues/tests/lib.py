import os
import tempfile
import shutil
import datetime
import pytz

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

import reversion

from organisations.tests.lib import create_test_problem

from ..lib import (changed_attrs,
                   changes_as_string,
                   changes_for_model,
                   base32_to_int,
                   int_to_base32,
                   MistypedIDException)
from ..models import Problem


class LibTests(TestCase):

    def setUp(self):
        self.old = {'status': Problem.NEW, 'publication_status': Problem.NOT_MODERATED}
        self.new = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED}

        self.old_missing = {'publication_status': Problem.NOT_MODERATED}
        self.new_missing = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED}

        self.old_unchanged = {'status': Problem.NEW, 'publication_status': Problem.NOT_MODERATED}
        self.new_unchanged = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.REJECTED}

    def test_changed_attrs_happy_path(self):
        expected_changed = {
            'status': [Problem.NEW, Problem.ACKNOWLEDGED],
            'publication_status': [Problem.NOT_MODERATED, Problem.PUBLISHED],
        }
        actual_changed = changed_attrs(self.old, self.new, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changed_attrs_missing_attrs(self):
        expected_changed = {
            'status': [None, Problem.ACKNOWLEDGED],
            'publication_status': [Problem.NOT_MODERATED, Problem.PUBLISHED],
        }
        actual_changed = changed_attrs(self.old_missing, self.new_missing, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changed_attrs_unchanged_attrs(self):
        expected_changed = {
            'status': [Problem.NEW, Problem.ACKNOWLEDGED],
            'publication_status': [Problem.NOT_MODERATED, Problem.REJECTED]
        }
        actual_changed = changed_attrs(self.old_unchanged, self.new_unchanged, Problem.REVISION_ATTRS)
        self.assertEqual(actual_changed, expected_changed)

    def test_changes_as_string_happy_path(self):
        expected = "Published and Acknowledged"
        changes = changed_attrs(self.old, self.new, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_unchanged_attrs(self):
        expected = "Rejected and Acknowledged"
        changes = changed_attrs(self.old_unchanged, self.new_unchanged, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_escalated(self):
        new_escalated = {'status': Problem.ESCALATED,
                         'publication_status': Problem.REJECTED,}

        expected = "Rejected and Escalated"
        changes = changed_attrs(self.old, new_escalated, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_escalated_acknowledged(self):
        old_escalated = {'status': Problem.ESCALATED,
                         'publication_status': Problem.REJECTED}

        new_escalated_acknowledged = {'status': Problem.ESCALATED_ACKNOWLEDGED,
                                      'publication_status': Problem.REJECTED}

        expected = "Acknowledged"
        changes = changed_attrs(old_escalated, new_escalated_acknowledged, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_as_string_escalated_resolved(self):
        old_escalated_acknowledged = {'status': Problem.ESCALATED_ACKNOWLEDGED,
                                      'publication_status': Problem.REJECTED}

        new_escalated_resolved = {'status': Problem.ESCALATED_RESOLVED,
                                  'publication_status': Problem.REJECTED}

        expected = "Resolved"
        changes = changed_attrs(old_escalated_acknowledged, new_escalated_resolved, Problem.REVISION_ATTRS)
        actual = changes_as_string(changes, Problem.TRANSITIONS)
        self.assertEqual(actual, expected)

    def test_changes_for_model(self):

        start_timestamp = datetime.datetime.now(pytz.utc)

        # Call the hompage to force the reversion.middleware to be loaded. This
        # is required for this test to pass in isolation. Not sure why.
        self.client.get('/')

        # Make a problem and give it some history
        with reversion.create_revision():
            problem = create_test_problem({'status': Problem.NEW,
                                           'publication_status': Problem.NOT_MODERATED})

        problem = Problem.objects.get(pk=problem.id)
        problem.status = Problem.ACKNOWLEDGED
        with reversion.create_revision():
            problem.save()

        problem = Problem.objects.get(pk=problem.id)
        problem.status = Problem.RESOLVED
        with reversion.create_revision():
            problem.save()

        problem = Problem.objects.get(pk=problem.id)
        problem.publication_status = Problem.PUBLISHED
        with reversion.create_revision():
            problem.save()

        end_timestamp = datetime.datetime.now(pytz.utc)

        expected_changes = [
            {'user': None, 'description': 'Acknowledged'},
            {'user': None, 'description': 'Resolved'},
            {'user': None, 'description': 'Published'},
        ]
        actual_changes = changes_for_model(problem)

        self.assertEqual(len(expected_changes), len(actual_changes))
        for index, change in enumerate(actual_changes):
            when = change['when']
            del change['when']
            self.assertEqual(change, expected_changes[index])
            self.assertGreaterEqual(when, start_timestamp)
            self.assertLessEqual(when, end_timestamp)

    def test_base32_roundtrip_conversion(self):
        self.assertEqual(829384, base32_to_int(int_to_base32(829384)))

    def test_base32_to_int_raises_exception_on_mistyped_characters(self):
        self.assertEqual(373536, base32_to_int('bcs0'))
        with self.assertRaises(MistypedIDException) as context_manager:
            base32_to_int('bcso')
        exception = context_manager.exception
        self.assertEqual(str(exception), '373536')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProblemImageTestBase(TestCase):

    @classmethod
    def setUpClass(cls):
        # Make the image fixture files available
        fixtures_dir = os.path.join(settings.PROJECT_ROOT, 'issues', 'tests', 'fixtures')
        cls.jpg = open(os.path.join(fixtures_dir, 'test.jpg'))
        cls.png = open(os.path.join(fixtures_dir, 'test.png'))
        cls.bmp = open(os.path.join(fixtures_dir, 'test.bmp'))
        cls.gif = open(os.path.join(fixtures_dir, 'test.gif'))

    @classmethod
    def tearDownClass(cls):
        # Close the image fixture files and wipe the temporary directory
        cls.jpg.close()
        cls.png.close()
        cls.gif.close()
        cls.png.close()

        if(os.path.exists(settings.MEDIA_ROOT)):
            shutil.rmtree(settings.MEDIA_ROOT)
