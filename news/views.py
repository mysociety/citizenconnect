from django.views.generic import DetailView

from .models import Article


class ArticleDetail(DetailView):

    model = Article
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super(ArticleDetail, self).get_context_data(**kwargs)
        context['recent_articles'] = Article.objects.exclude(pk=context['article'].id).order_by('-published')[:3]
        return context
