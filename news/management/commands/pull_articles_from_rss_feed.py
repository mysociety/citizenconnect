from dateutil import parser
import feedparser

from django.core.management.base import BaseCommand
from django.conf import settings

from ...models import Article


class Command(BaseCommand):
    args = "<file|url>"
    help = "Import articles from the given file or url"

    def handle(self, *args, **options):
        if len(args) > 0:
            feed_url = args[0]
        else:
            feed_url = settings.NHS_RSS_FEED_URL

        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            if not Article.objects.filter(guid=entry.id).exists():
                if len(entry.enclosures) > 0:
                    image = entry.enclosures[0].get('url', '')
                else:
                    image = ''

                Article.objects.create(
                    guid=entry.id,
                    title=entry.title,
                    description=entry.summary,
                    content=entry.content[0].value,
                    author=entry.author,
                    published=parser.parse(entry.published),
                    image=image
                )
