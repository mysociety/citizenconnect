import os
import urllib
from dateutil import parser
import re

import feedparser

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File

from citizenconnect.models import delete_uploaded_file

from ...models import Article


class Command(BaseCommand):
    args = "<file|url>"
    help = "Import articles from the given file or url"

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        if len(args) > 0:
            feed_url = args[0]
        else:
            feed_url = settings.NHS_RSS_FEED_URL

        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            try:
                article = Article.objects.get(guid=entry.id)
                if verbosity >= 2:
                    self.stdout.write("Updating Article guid={0}\n".format(article.id))
            except Article.DoesNotExist:
                article = Article(guid=entry.guid)
                if verbosity >= 2:
                    self.stdout.write("Creating Article guid={0}\n".format(article.id))

            article.title = entry.title
            article.description = entry.summary
            article.content = entry.content[0].value.replace(settings.BLOG_FILES_URL, settings.PROXIED_BLOG_FILES_URL)
            article.author = entry.author
            article.published = parser.parse(entry.published)

            # Save the article first
            article.save()

            # Then try to download the image
            if entry.enclosures:
                # Enclosures can contain videos too, find the first image
                image_content_type_regex = re.compile("^image/")
                image_enclosure = None
                for enclosure in entry.enclosures:
                    if hasattr(enclosure, 'type') and image_content_type_regex.match(enclosure.type):
                        image_enclosure = enclosure
                        break

                if image_enclosure:
                    image_url = image_enclosure.get('url', '')
                    if image_url:
                        try:
                            if verbosity >= 2:
                                self.stdout.write("Downloading new image for Article guid={0}\n".format(article.id))
                            # Get the new image
                            (temp_image_file, headers) = urllib.urlretrieve(image_url)
                            image_filename = os.path.basename(image_url)
                            # Delete the old image if there is one
                            if article.image:
                                if verbosity >= 2:
                                    self.stdout.write("Deleting existing image for Article guid={0}\n".format(article.id))
                                storage = article.image.storage
                                path = article.image.path
                                name = article.image.name
                                delete_uploaded_file(storage, path, name)
                            # Save the new one in it's place
                            article.image.save(
                                image_filename,
                                File(open(temp_image_file))
                            )
                            article.save()
                            os.remove(temp_image_file)
                        except Exception as e:
                            # On any exception, just ignore the image
                            if verbosity >= 1:
                                self.stderr.write("Skipping image for %s: %s\n" % (article.title, e))
