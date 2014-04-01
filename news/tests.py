import os
import re
import urllib
import shutil
import tempfile
from StringIO import StringIO

from mock import MagicMock

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.conf import settings

from .models import Article


class ArticleModelTest(TestCase):
    def test_article_model_exists(self):
        article = Article.objects.create(
            title="Test title",
            description="Test description",
            published=timezone.now()
        )
        self.assertEqual("Test title", article.title)
        self.assertEqual("Test description", article.description)


class PullArticlesFromRssFeedTests(TestCase):

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.fixtures_dir = os.path.join(settings.PROJECT_ROOT, 'news', 'tests', 'fixtures')
        self.rss_feed = os.path.join(self.fixtures_dir, 'news_feed.xml')

        # Sample image file
        sample_article_image = os.path.join(self.fixtures_dir, 'sample-article-image.jpg')
        # Copy it to tempfile because the import expects a tempfile to delete
        (handle, filename) = tempfile.mkstemp(".jpg")
        self.temp_article_image = filename
        shutil.copyfile(sample_article_image, self.temp_article_image)

        # Mock urllib.urlretrieve so that our command can call it
        self._original_urlretrieve = urllib.urlopen
        # urlretrieve returns a tuple of a file and some headers
        urllib.urlretrieve = MagicMock(return_value=(self.temp_article_image, None))

    def tearDown(self):
        # Undo the mocking of urlretrieve
        urllib.urlretrieve = self._original_urlretrieve

        # Wipe the temporary files
        if(os.path.exists(self.temp_article_image)):
            os.remove(self.temp_article_image)

    def call_command(self, *args, **options):
        options['stdout'] = self.stdout
        options['stderr'] = self.stderr
        call_command(*args, **options)

    def test_pulls_entries_from_rss_feed(self):
        self.assertEqual(0, Article.objects.count())
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        self.assertEqual(2, Article.objects.count())

    def test_doesnt_create_entries_twice(self):
        self.assertEqual(0, Article.objects.count())
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        self.assertEqual(2, Article.objects.count())

    @override_settings(
        BLOG_FILES_URL='http://www.example.com/files',
        PROXIED_BLOG_FILES_URL='/careconnect/files'
    )
    def test_creates_entries_correctly(self):
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        article = Article.objects.get(guid='http://blogs.mysociety.org/careconnect/?p=1')
        self.assertEqual("Hello world!", article.title)
        self.assertEqual("Welcome to mySociety Blog Network. This is your first post. Edit or delete it, then start blogging!", article.description)
        self.assertEqual('<p>Welcome to <a href="http://blogs.mysociety.org/">mySociety Blog Network</a>. This is your first post. Edit or delete it, then start blogging! <img src="{0}/2013/07/test-image.jpg" /></p>'.format(settings.PROXIED_BLOG_FILES_URL), article.content)
        self.assertEqual("steve", article.author)

        # Test the image was added
        image_filename = article.image.url
        image_filename_regex = re.compile('article_images/\w{2}/\w{2}/[0-9a-f]{32}.jpg', re.I)
        self.assertRegexpMatches(image_filename, image_filename_regex)

    def test_updates_existing_entries(self):
        article = Article(guid='http://blogs.mysociety.org/careconnect/?p=1')
        article.title = "Foo"
        article.author = "Bar"
        article.published = timezone.now()
        article.save()
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        article = Article.objects.get(guid='http://blogs.mysociety.org/careconnect/?p=1')
        self.assertEqual("Hello world!", article.title)
        self.assertEqual("steve", article.author)

    def test_image_optional(self):
        self.call_command('get_articles_from_rss_feed', self.rss_feed)
        article = Article.objects.get(guid='http://blogs.mysociety.org/careconnect/?p=2')  # This one has no image
        self.assertFalse(bool(article.image))

    def test_deals_with_image_errors(self):
        # Mock urlretrieve to throw an error
        urllib.urlretrieve.side_effect = Exception("Boom!")

        # Load the data in
        self.call_command('get_articles_from_rss_feed', self.rss_feed)

        # Check it worked, but we have no image
        self.assertEqual(Article.objects.count(), 2)
        article = Article.objects.get(guid='http://blogs.mysociety.org/careconnect/?p=2')
        self.assertFalse(bool(article.image))

        urllib.urlretrieve.side_effect = None

    def test_ignores_videos_in_multiple_enclosures(self):
        self.multiple_enclosures_rss_feed = os.path.join(self.fixtures_dir, 'news_feed_multiple_enclosures.xml')

        # Load the data in
        self.call_command('get_articles_from_rss_feed', self.multiple_enclosures_rss_feed)

        # Check it worked and we picked the right enclosure
        self.assertEqual(Article.objects.count(), 2)
        article = Article.objects.get(guid='http://blogs.mysociety.org/careconnect/?p=1')
        image_filename = article.image.url
        image_filename_regex = re.compile('article_images/\w{2}/\w{2}/[0-9a-f]{32}.jpg', re.I)
        self.assertRegexpMatches(image_filename, image_filename_regex)


class ArticleDetailViewTests(TestCase):

    def setUp(self):
        # Create some articles
        self.articles = []
        for i in range(5):
            article_number = i + 1
            self.articles.append(Article.objects.create(
                guid="article{0}".format(article_number),
                title="test article {0}".format(article_number),
                description="Short description {0}".format(article_number),
                content="<p>Short description {0}</p>".format(article_number),
                author="Author {0}".format(article_number),
                published=timezone.now(),
            ))
        self.article_detail_url = reverse('article-view', kwargs={'cobrand': 'choices', 'pk': self.articles[0].id})

    def test_page_exists(self):
        resp = self.client.get(self.article_detail_url)
        self.assertEqual(resp.status_code, 200)

    def test_page_shows_article_details(self):
        resp = self.client.get(self.article_detail_url)
        self.assertContains(resp, self.articles[0].title)
        self.assertContains(resp, self.articles[0].author)
        self.assertContains(resp, self.articles[0].content)

    def test_page_shows_other_articles(self):
        # We expect the newest three articles to be shown in the sidebar,
        # but not including the one currently shown in the main section
        newest_article_url = reverse('article-view', kwargs={'cobrand': 'choices', 'pk': self.articles[4].id})
        expected_articles = [self.articles[3], self.articles[2], self.articles[1]]

        resp = self.client.get(newest_article_url)

        self.assertNotContains(resp, '<a href="{0}'.format(newest_article_url))
        for article in expected_articles:
            expected_url = reverse('article-view', kwargs={'cobrand': 'choices', 'pk': article.id})
            expected_link = '<a href="{0}'.format(expected_url)
            self.assertContains(resp, expected_link)
