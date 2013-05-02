from django.core.management.base import BaseCommand
from django.conf import settings

from ...reviews_api import ReviewsAPI
from ...models import Review, OrganisationFromApiDoesNotExist


class Command(BaseCommand):
    help = 'Fetch reviews from choices API'

    # @transaction.commit_manually
    def handle(self, *args, **options):

        for type in settings.ORGANISATION_TYPES:
            reviews = ReviewsAPI(organisation_type=type)

            for review in reviews:
                try:
                    Review.upsert_from_api_data(review)
                except OrganisationFromApiDoesNotExist:
                    pass
