from django.utils import timezone
from datetime import timedelta

from django.core.management.base import BaseCommand

from ...models import Review


class Command(BaseCommand):
    help = "Remove any reviews that were sent to the API over 2 weeks ago"

    def handle(*args, **options):
        now = timezone.now()
        two_weeks_ago = now - timedelta(weeks=2)
        Review.objects.filter(last_sent_to_api__lt=two_weeks_ago).delete()
