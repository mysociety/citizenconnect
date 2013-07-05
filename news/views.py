from django.views.generic import DetailView, ListView

from .models import Article


class ArticleDetail(DetailView):

    model = Article

    def get_context_data(self, **kwargs):
        context = super(ArticleDetail, self).get_context_data(**kwargs)
        context['recent_articles'] = Article.objects.order_by('-published')[:3]
        return context


class ArticleList(ListView):

    model = Article

    def get_queryset(self):
        """Order so that it is most recent first"""
        qs = super(ArticleList, self).get_queryset()
        return qs.order_by('-published')
