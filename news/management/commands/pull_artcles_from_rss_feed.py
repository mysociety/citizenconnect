from datetime import datetime
from time import mktime
import feedparser

from django.core.management.base import BaseCommand

from ...models import Article


class Command(BaseCommand):
    def handle(self, *args, **options):
        feed = feedparser.parse(args[0])
        for entry in feed.entries:
            Article.objects.create(
                title=entry.title,
                description=entry.summary,
                content=entry.content,
                author=entry.author,
                published=datetime.fromtimestamp(mktime(entry.published_parsed))
            )
