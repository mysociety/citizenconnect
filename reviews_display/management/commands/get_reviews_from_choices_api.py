import datetime
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from ...reviews_api import ReviewsAPI
from ...models import Review, OrganisationFromApiDoesNotExist, RepliedToReviewDoesNotExist


class Command(NoArgsCommand):
    help = 'Fetch reviews from choices API (by default those changed in the last seven days)'

    option_list = NoArgsCommand.option_list + (
        make_option('--all',
                    action='store_true',
                    dest='fetch_all',
                    default=False,
                    help='Fetch all reviews, not just those changed in last seven days'),
    )

    # @transaction.commit_manually
    def handle_noargs(self, *args, **options):
        verbosity = int(options.get('verbosity'))

        if options['fetch_all']:
            if verbosity >= 2:
                self.stdout.write("Fetching most recent 10,000 reviews\n")
            api_args = dict(max_fetch=10000)
        else:
            if verbosity >= 2:
                self.stdout.write("Fetching up to 100 reviews from the past week\n")
            one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
            api_args = dict(since=one_week_ago, max_fetch=100)

        for type in settings.ORGANISATION_TYPES:
            reviews = ReviewsAPI(organisation_type=type, **api_args)

            for review in reviews:
                try:
                    Review.upsert_or_delete_from_api_data(review, type)
                except OrganisationFromApiDoesNotExist:
                    pass
                except RepliedToReviewDoesNotExist, e:
                    if verbosity >= 1:
                        self.stdout.write('RepliedToReviewDoesNotExist: ' + str(e) + " - skipping\n")
