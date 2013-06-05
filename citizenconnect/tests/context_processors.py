from mock import MagicMock

from django.test import TestCase
from django.conf import settings

from ..context_processors import add_site_section


class ContextProcessorTests(TestCase):

    def test_add_site_section(self):

        tests = {
            # path: expected site_section
            '/':                     None,
            '/foo/bar':              None,

            # These should probably not be styled
            '/foo/summary':          None,
            '/foo/map':              None,
            '/foo/choose-dashboard': None,

            '/foo/reviews':                    'review',
            '/foo/reviews/blahblah':           'review',
            '/foo/common-questions':           'question',
            '/foo/common-questions/blahblah':  'question',
            '/foo/problem':                    'problem',
            '/foo/problem/blahblah':           'problem',

            # regressions for issues found with real urls
            '/foo/problems/H85031': 'problem',
        }

        for path, site_section in tests.items():

            # create a fake request that has the path we're testing
            request = MagicMock(path=path)

            # use this to run the context_processor
            context = add_site_section( request )

            # check that we get the expected result.
            self.assertEqual(
                context.get('site_section'),
                site_section,
                "path '{0}' should give site_section '{1}'".format(path, site_section)
            )
