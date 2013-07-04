from django.test import TestCase
from django.utils import timezone

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
