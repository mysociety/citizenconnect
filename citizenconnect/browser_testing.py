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

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        # cls.driver = webdriver.Chrome()
        super(SeleniumTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super(SeleniumTestCase, cls).tearDownClass()

    def full_url(self, path):
        """Add the path given to the live_server_url"""
        return self.live_server_url + path
