from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^map$', Map.as_view(), name='org-map'),
    url(r'^pick-provider$', PickProviderBase.as_view(), name='org-pick-provider'),
    url(r'^summary$', Summary.as_view(), name='org-all-summary'),
    url(r'^summary/(?P<ods_code>\w+)$', OrganisationSummary.as_view(), name='public-org-summary'),
    url(r'^problems/(?P<ods_code>\w+)$', OrganisationProblems.as_view(), name='public-org-problems'),
)
