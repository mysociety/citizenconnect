from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^map$', Map.as_view(), name='org-map'),
    url(r'^pick-provider$', PickProvider.as_view(), name='org-pick-provider'),
    url(r'^provider-results$', ProviderResults.as_view(), name='org-provider-results'),
    url(r'^summary$', Summary.as_view(), name='org-all-summary'),
    url(r'^summary/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', OrganisationSummary.as_view(), name='org-summary'),
)
