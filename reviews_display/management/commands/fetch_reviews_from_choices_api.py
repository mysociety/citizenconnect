from pprint import pprint

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.db import transaction

from ...reviews_api import ReviewsAPI
from ...models import Review, OrganisationFromApiDoesNotExist


class Command(BaseCommand):
    help = 'Fetch reviews from choices API'

    # @transaction.commit_manually
    def handle(self, *args, **options):

        reviews = ReviewsAPI()

        for review in reviews:
            # print "Looking at {api_posting_id} ({api_category})".format(**review)
            try:
                Review.upsert_from_api_data(review)
            except OrganisationFromApiDoesNotExist:
                pass
