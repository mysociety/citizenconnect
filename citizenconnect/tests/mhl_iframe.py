from django.test import TestCase

from django.core.urlresolvers import reverse


class MHLIframeTests(TestCase):

    def setUp(self):
        self.iframe_url = reverse('mhl-iframe')

    def test_doesnt_include_nav(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<ul class="site-nav">')

    def test_doesnt_include_mhl_header(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div id="myhealthlondon-header"')

    def test_doesnt_include_footer(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div class="footer">')

    def test_doesnt_include_mhl_footer(self):
        resp = self.client.get(self.iframe_url)
        self.assertNotContains(resp, '<div id="myhealthlondon-footer">')

    def test_includes_cta_buttons_with_target_blank(self):
        reviews_url = reverse('reviews-pick-provider', kwargs={'cobrand': 'myhealthlondon'})
        expected_reviews_cta = '<a target="_blank" href="https://www.myhealth.london.nhs.uk{0}"'.format(reviews_url)

        expected_questions_cta = '<a target="_blank" href="https://www.myhealth.london.nhs.uk/faq-page"'

        problems_url = reverse('problems-pick-provider', kwargs={'cobrand': 'myhealthlondon'})
        expected_problems_cta = '<a target="_blank" href="https://www.myhealth.london.nhs.uk{0}"'.format(problems_url)

        resp = self.client.get(self.iframe_url)

        self.assertContains(resp, expected_reviews_cta)
        self.assertContains(resp, expected_questions_cta)
        self.assertContains(resp, expected_problems_cta)
