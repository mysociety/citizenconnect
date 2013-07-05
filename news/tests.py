from StringIO import StringIO

from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command

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

    def test_pulls_entries_from_rss_feed(self):
        self.assertEqual(0, Article.objects.count())
        call_command('pull_artcles_from_rss_feed', stdout=self.stdout, stderr=self.stderr)
        self.assertEqual(1, Article.objects.count())
