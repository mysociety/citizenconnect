from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url(r'^$', ArticleList.as_view(), name='article-list'),
    url(r'^/(?P<pk>\d+)$', ArticleDetail.as_view(), name='article-view'),
)
