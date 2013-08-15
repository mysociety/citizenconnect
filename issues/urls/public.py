from django.conf.urls import patterns, include, url

from ..views import *

urlpatterns = patterns('',
    url(r'^problem/pick-provider$', ProblemPickProvider.as_view(), name='problems-pick-provider'),
    url(r'^problem/problem-form/(?P<ods_code>\w+)$', ProblemCreate.as_view(), name='problem-form'),
    url(r'^problem/(?P<pk>\d+)$', ProblemDetail.as_view(), name='problem-view'),
    # survey responses can be 'y' for yes, 'n' for no, and 'd' for don't want to answer
    url(r'^survey/(?P<response>(y|n|d))/(?P<id>[0-9A-Za-z]+)-(?P<token>.+)$', ProblemSurvey.as_view(), name='survey-form'),
)
