import logging
import os
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User

from ..models import Organisation, Trust, CCG

from organisations import auth
from issues.models import Problem

class CsvImportTests(TestCase):

    def test_happy_path(self):
        # Quiet logging for this test - there a CCGs loaded that don't have email
        logging.disable(logging.CRITICAL)

        call_command('load_ccgs_from_spreadsheet', 'organisations/tests/samples/ccgs.csv')
        self.assertEqual(CCG.objects.count(), 3)

        call_command('load_trusts_from_spreadsheet', 'organisations/tests/samples/trusts.csv')
        self.assertEqual(Trust.objects.count(), 3)
        self.assertEqual(CCG.objects.get(name="Ascot CCG").trusts.count(), 2)
        self.assertEqual(CCG.objects.get(name="Banbridge CCG").trusts.count(), 1)
        self.assertEqual(CCG.objects.get(name="Chucklemere CCG").trusts.count(), 0)

        call_command('load_organisations_from_spreadsheet', 'organisations/tests/samples/organisations.csv')
        self.assertEqual(Organisation.objects.count(), 3)
        self.assertEqual(Trust.objects.get(name="Ascot North Trust").organisations.count(), 2)
        self.assertEqual(Trust.objects.get(name="Ascot South Trust").organisations.count(), 1)
        self.assertEqual(Trust.objects.get(name="Banbridge North Trust").organisations.count(), 0)

