from mock import MagicMock

from django.test import TestCase
from django.conf import settings

from ..context_processors import add_site_section


class ContextProcessorTests(TestCase):

    def test_add_site_section(self):

        url_prefix = '/' + settings.ALLOWED_COBRANDS[0] + '/'

        tests = {
            # path: expected site_section
            '/':                       None,
            '/foo/bar':                None,
            '/not-a-cobrand/problems': None,

            url_prefix + 'reviews':                    'review',
            url_prefix + 'reviews/blahblah':           'review',
            url_prefix + 'common-questions':           'question',
            url_prefix + 'common-questions/blahblah':  'question',
            url_prefix + 'problem':                    'problem',
            url_prefix + 'problem/blahblah':           'problem',

            # regressions for issues found with real urls
            url_prefix + 'problems/H85031': 'problem',
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
