from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^pick-provider$', PickProvider.as_view(), name='problems-pick-provider'),
    url(r'^provider-results$', ProviderResults.as_view(), name='problems-provider-results'),
    url(r'^problem-form/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', ProblemForm.as_view(), name='problem-form'),
    url(r'^problem-confirm$', ProblemConfirm.as_view(), name='problem-confirm'),
    url(r'^(?P<problem_id>\d+)$', ProblemPublicView.as_view(), name='problem-view')
)


