import os
from StringIO import StringIO

from django.test import TestCase
from django.utils import timezone
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

    def call_command(self, *args, **options):
        options['stdout'] = self.stdout
        options['stderr'] = self.stderr
        call_command(*args, **options)

    def test_pulls_entries_from_rss_feed(self):
        self.assertEqual(0, Article.objects.count())
        self.call_command('pull_articles_from_rss_feed', self.rss_feed)
        self.assertEqual(1, Article.objects.count())

    def test_doesnt_create_entries_twice(self):
        self.assertEqual(0, Article.objects.count())
        self.call_command('pull_articles_from_rss_feed', self.rss_feed)
        self.call_command('pull_articles_from_rss_feed', self.rss_feed)
        self.assertEqual(1, Article.objects.count())
