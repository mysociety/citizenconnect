from django.test import TestCase
from django.test.utils import override_settings

from django.conf import settings
from django.core.urlresolvers import reverse


class DevHomepageTests(TestCase):
    """
    Test that '/' is the dev_homepage when DEBUG = True, and that it redirects
    to '/<primary_cobrand> when not.
    """

    def setUp(self):
        self.homepage_url = reverse('homepage-selector')

    # Note - we use STAGING rather than DEBUG because DEBUG is always False when
    # runing Django tests.

    @override_settings(STAGING=True)
    def test_with_staging_true(self):
        resp = self.client.get(self.homepage_url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'cobrand_choice.html')

    @override_settings(STAGING=False)
    def test_with_staging_false(self):
        resp = self.client.get(self.homepage_url, follow=True)
        primary_cobrand = settings.ALLOWED_COBRANDS[0]
        self.assertEqual(resp.redirect_chain, [('http://testserver/'+primary_cobrand,301)])

