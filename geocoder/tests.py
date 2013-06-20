# import logging
# import os
# import sys
# from StringIO import StringIO

from django.test import TestCase
from django.core.management import call_command
from django.forms.models import model_to_dict

from .models import Place


class CsvImportTests(TestCase):

    def setUp(self):
        # Paths to the various sample data files
        csv_dir = 'geocoder/test_data/'
        self.os_locator_data_filename = csv_dir + 'OS_Locator2013_1_OPEN_sample.txt'

    def test_os_locator(self):

        call_command('import_from_OS_locator', self.os_locator_data_filename)
        self.assertEqual(Place.objects.count(), 10)

        place = Place.objects.get(name="BEVAN COURT")
        self.assertEqual(
            model_to_dict(place, exclude=['centre','id']),
            {
                'name': 'BEVAN COURT',
                'context_name': 'BEVAN COURT, Waddon',
                'source': Place.SOURCE_OS_LOCATOR,
            }
        )
        self.assertEqual( place.centre.x, -0.11587620309898315 )
        self.assertEqual( place.centre.y, 51.361488927177462   )
