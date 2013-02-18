from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^pick-provider$', PickProvider.as_view(), name='problems-pick-provider'),
    url(r'^problem-form/(?P<ods_code>\w+)$', ProblemCreate.as_view(), name='problem-form'),
    url(r'^(?P<pk>\d+)$', ProblemDetail.as_view(), name='problem-view')
)
