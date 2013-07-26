import os
import urllib
from dateutil import parser

import feedparser

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

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
                # Save the article first
                article = Article.objects.create(
                    guid=entry.id,
                    title=entry.title,
                    description=entry.summary,
                    content=entry.content[0].value,
                    author=entry.author,
                    published=parser.parse(entry.published)
                )
                # Then try to download the image
                if len(entry.enclosures) > 0:
                    image_url = entry.enclosures[0].get('url', '')
                    if image_url:
                        try:
                            (temp_image_file, headers) = urllib.urlretrieve(image_url)
                            image_filename = os.path.basename(image_url)
                            article.image.save(
                                image_filename,
                                File(open(temp_image_file))
                            )
                            article.save()
                            os.remove(temp_image_file)
                        except Exception as e:
                            # On any exception, just ignore the image
                            self.stderr.write("Skipping image for %s: %s\n" % (article.title, e))
