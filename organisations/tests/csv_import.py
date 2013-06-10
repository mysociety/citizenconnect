import logging
import os
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User

from ..models import Organisation, CCG

from organisations import auth
from issues.models import Problem

class CsvImportTests(TestCase):

    def test_happy_path(self):
        # Quiet logging for this test - there a CCGs loaded that don't have email
        logging.disable(logging.CRITICAL)

        call_command('load_ccgs_from_spreadsheet', 'organisations/tests/samples/ccgs.csv')
        self.assertEqual(CCG.objects.count(), 3)
