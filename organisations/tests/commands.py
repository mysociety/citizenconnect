import logging
import os
import sys
from StringIO import StringIO

from django.test import TestCase
from django.core import mail
from django.core.management import call_command
from django.conf import settings
from django.contrib.auth.models import User

from .lib import create_test_organisation, create_test_ccg, create_test_service, create_test_problem, create_test_trust
from .choices_api import ExampleFileAPITest
from ..models import Organisation

from organisations import auth
from issues.models import Problem


class DevNull(object):
    def write(self, data):
        pass


class GetOrganisationRatingsFromChoicesAPITests(ExampleFileAPITest):

    @classmethod
    def setUpClass(cls):
        # Fixture for a particular organisation
        cls._example_file = '41265.xml'
        super(GetOrganisationRatingsFromChoicesAPITests, cls).setUpClass()

    def _call_command(self, *args, **opts):
        call_command('get_organisation_ratings_from_choices_api', *args, **opts)

    def test_happy_path(self):
        # Add an organisation to pull the ratings for
        organisation = create_test_organisation({'organisation_type': 'hospitals',
                                                 'choices_id': 41265})
        self.assertEqual(organisation.average_recommendation_rating, None)

        stdout = StringIO()
        self._call_command(stdout=stdout)
        self.assertEquals(stdout.getvalue(), 'Updated rating for organisation Test Organisation\n')

        organisation = Organisation.objects.get(pk=organisation.id)

        # Because we store things in a float field, there will be some rounding
        # that happens on different systems, but realistically, 3 D.P. is
        # sufficient - I just didn't want to be explicit so that we keep the
        # data they give us as it is.
        self.assertAlmostEqual(organisation.average_recommendation_rating, 4.2857142857142856, places=3)
