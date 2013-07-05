from dateutil import parser
import feedparser

from django.core.management.base import BaseCommand

from ...models import Article


class Command(BaseCommand):
    args = "<file|url>"
    help = "Import articles from the given file or url"
    def handle(self, *args, **options):
        feed = feedparser.parse(args[0])
        for entry in feed.entries:
            try:
                Article.objects.get(guid=entry.id)
            except Article.DoesNotExist:
                Article.objects.create(
                    guid=entry.id,
                    title=entry.title,
                    description=entry.summary,
                    content=entry.content[0].value,
                    author=entry.author,
                    published=parser.parse(entry.published)
                )
