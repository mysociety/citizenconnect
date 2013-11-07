import subprocess
import os

from django.test import TestCase
from django.conf import settings


class CheckRequirements(TestCase):

    def test_requirements_matches_pip_freeze(self):
        p = subprocess.Popen(
            ['pip', 'freeze'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        out, err = p.communicate()

        requirements_path = os.path.join(settings.PROJECT_ROOT, 'requirements.txt')
        with open(requirements_path, 'r') as requirements_file:
            requirements = requirements_file.read()
            self.assertEqual(requirements, out)
