from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = "Import articles from NHS_RSS_FEED_URL"
    def handle(self, *args, **options):
        call_command('pull_articles_from_rss_feed', settings.NHS_RSS_FEED_URL)
