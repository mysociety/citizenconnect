import os
import datetime
import pytz

from django.conf import settings
from django.test import TestCase

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
        self.old = {'status': Problem.NEW, 'publication_status': Problem.NOT_MODERATED, 'requires_second_tier_moderation': False}
        self.new = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED, 'requires_second_tier_moderation': False}

        self.old_missing = {'publication_status': Problem.NOT_MODERATED}
        self.new_missing = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.PUBLISHED, 'requires_second_tier_moderation': False}

        self.old_unchanged = {'status': Problem.NEW, 'publication_status': Problem.NOT_MODERATED, 'requires_second_tier_moderation': False}
        self.new_unchanged = {'status': Problem.ACKNOWLEDGED, 'publication_status': Problem.REJECTED, 'requires_second_tier_moderation': False}

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
            'requires_second_tier_moderation': [None, False],
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

    def changes_as_string_requires_second_tier_moderation(self):
        old = {
            'status': Problem.NOT_MODERATED,
            'requires_second_tier_moderation': False
        }

        new = {
            'status': Problem.NOT_MODERATED,
            'requires_second_tier_moderation': True
        }

        expected = "Referred"
        changes = changed_attrs(old, new, Problem.REVISION_ATTRS)
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
        problem.requires_second_tier_moderation = True
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
            {'user': None, 'description': 'Referred'},
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


class ProblemImageTestBase(TestCase):
    """
    Base class for testing things related to images on problems.
    Use where you need access to dummy image files, and override_settings
    MEDIA_ROOT to put them in a temporary folder.
    """

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
