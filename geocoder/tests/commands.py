import sys

from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django.forms.models import model_to_dict

from ..models import Place

from django.contrib.gis.geos import Point


class DevNull(object):
    def write(self, data):
        pass


class GeocoderCsvImportTests(TestCase):

    def setUp(self):

        # Mute stderr (the progress bar output)
        self.old_stderr = sys.stderr
        sys.stderr = DevNull()

        # Paths to the various sample data files
        csv_dir = 'geocoder/tests/test_data/'
        self.os_locator_data_filename       = csv_dir + 'OS_Locator2013_1_OPEN_sample.txt'
        self.os_50k_gazetteer_data_filename = csv_dir + '50kgaz2013_sample.txt'

    def tearDown(self):
        sys.stderr = self.old_stderr

    @override_settings(GEOCODER_BOUNDING_BOXES=(
        # xmin, ymin, xmax, ymax
        ( -0.8, 51.1, 0.6,  51.8 ), # London
    ))
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

    @override_settings(GEOCODER_BOUNDING_BOXES=(
        # xmin, ymin, xmax, ymax
        ( -0.8, 51.1, 0.6,  51.8 ), # London
    ))
    def test_50k_gazetteer(self):

        call_command('import_from_OS_50k_gazetteer', self.os_50k_gazetteer_data_filename)
        self.assertEqual(Place.objects.count(), 10)

        place = Place.objects.get(name="Farringdon Station")
        self.assertEqual(
            model_to_dict(place, exclude=['centre','id']),
            {
                'name': 'Farringdon Station',
                'context_name': 'Farringdon Station, City of London',
                'source': Place.SOURCE_OS_50K_GAZETEER,
            }
        )
        self.assertEqual( place.centre.x, -0.1061755458136722 )
        self.assertEqual( place.centre.y, 51.517070389322676   )

