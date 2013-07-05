from django.test import TestCase
from django.utils import timezone
from django.core.urlresolvers import reverse

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


class ArticleDetailViewTests(TestCase):

    def setUp(self):
        # Create some articles
        self.articles = []
        for i in range(5):
            article_number = i + 1
            self.articles.append(Article.objects.create(
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
