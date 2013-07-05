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
            if not Article.objects.filter(guid=entry.id).exists():
                Article.objects.create(
                    guid=entry.id,
                    title=entry.title,
                    description=entry.summary,
                    content=entry.content[0].value,
                    author=entry.author,
                    published=parser.parse(entry.published)
                )
