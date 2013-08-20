from django.utils import timezone
from datetime import timedelta

from django.core.management.base import NoArgsCommand

from ...models import Review


class Command(NoArgsCommand):
    help = "Remove any reviews that were sent to the API over 2 weeks ago"

    def handle_noargs(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        now = timezone.now()
        two_weeks_ago = now - timedelta(weeks=2)
        reviews_to_delete = Review.objects.filter(last_sent_to_api__lt=two_weeks_ago)

        if verbosity >= 2:
            self.stdout.write("Removing {0} reviews\n".format(reviews_to_delete.count()))

        reviews_to_delete.delete()
