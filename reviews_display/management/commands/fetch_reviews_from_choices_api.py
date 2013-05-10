import datetime

from django.core.management.base import BaseCommand
from django.conf import settings

from ...reviews_api import ReviewsAPI
from ...models import Review, OrganisationFromApiDoesNotExist


class Command(BaseCommand):
    help = 'Fetch reviews from choices API'

    # @transaction.commit_manually
    def handle(self, *args, **options):

        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)

        for type in settings.ORGANISATION_TYPES:
            reviews = ReviewsAPI(organisation_type=type, since=one_week_ago, max_fetch=100)

            for review in reviews:
                try:
                    Review.upsert_from_api_data(review)
                except OrganisationFromApiDoesNotExist:
                    pass
