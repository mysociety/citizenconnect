import re

from django.test import TestCase

from ..models import partitioned_upload_path_and_obfuscated_name


class CitizenConnectModelTests(TestCase):

    def test_image_upload_to_partition_dir(self):

        seen = set()

        for i in range(10):
            partition = partitioned_upload_path_and_obfuscated_name(None, "some-file.jpg")
            seen.add(partition)

            # Note that django always divides FileField paths with unix separators
            regex = re.compile('\w{2}/\w{2}/[0-9a-f]{32}.jpg', re.I)
            self.assertRegexpMatches(partition, regex)

        self.assertTrue(len(seen) > 1)
