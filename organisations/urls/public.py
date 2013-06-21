from django.conf.urls import patterns, url

from organisations.views.base import *
from organisations.views.organisations import *

urlpatterns = patterns(
    '',
    url(r'^map$', Map.as_view(), name='org-map'),
    url(r'^map/(?P<ods_code>\w+)$', MapOrganisation.as_view(), name='single-org-map'),
    url(r'^pick-provider$', OrganisationPickProvider.as_view(), name='org-pick-provider'),
    url(r'^summary$', Summary.as_view(), name='org-all-summary'),
    url(r'^summary/(?P<ods_code>\w+)$', OrganisationSummary.as_view(), name='public-org-summary'),
    url(r'^problems/(?P<ods_code>\w+)$', OrganisationProblems.as_view(), name='public-org-problems'),
)
