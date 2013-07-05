from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url(r'^news$', ArticleList.as_view(), name='article-list'),
    url(r'^news/(?P<pk>\d+)$', ArticleDetail.as_view(), name='article-view'),
)
