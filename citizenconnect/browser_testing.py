import sys
import os

from selenium import webdriver

from django.test import LiveServerTestCase
from django.utils import unittest


@unittest.skipIf(
    os.environ.get('SKIP_BROWSER_TESTS'),
    "Skipping selenium tests because env 'SKIP_BROWSER_TESTS' is true"
)
class SeleniumTestCase(LiveServerTestCase):

    """
    from citizenconnect.browser_testing import SeleniumTestCase

    class FooTests(FooBase, SeleniumTestCase):

        def setUp(self):
            super(FooTests, self).setUp()

        def test_foo(self):
            d = self.driver
            d.get(self.full_url(self.foo_url))

            # drop into a nice REPL shell to test commands and see the results
            # in the browser straight away.
            import IPython
            IPython.embed()

            # some useful docs
            # https://gist.github.com/1047207/908fc2dac70e1c2d0c597e5914a1ddbd76f4bb96

            # really obscure commands can be accessed using ActionChains
            # directly
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(driver).move_to_element_with_offset(
                element, 10, 8).click(None).perform()
    """

    @classmethod
    def setUpClass(cls):
        # We can't use Firefox or IE as the move_to_element_with_offset
        # commend is not supported by them. Ues Chrome instead
        cls.driver = webdriver.Chrome()
        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def full_url(self, path):
        """Add the path given to the live_server_url"""
        return self.live_server_url + path
