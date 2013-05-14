from django.core.management.base import NoArgsCommand

from ...models import Review


class Command(NoArgsCommand):
    help = 'Delete reviews from the database that are older than NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS'

    def handle_noargs(self, *args, **options):
        Review.delete_old_reviews()
