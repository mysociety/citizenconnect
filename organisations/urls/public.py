from django.conf.urls import patterns, url

from reviews_display.views import OrganisationReviews
from issues.views import OrganisationProblems

from organisations.views.base import *
from organisations.views.organisations import *

urlpatterns = patterns(
    '',
    url(r'^map$', Map.as_view(), name='org-map'),
    url(r'^map/search$', MapSearch.as_view(), name='org-map-search'),
    url(r'^map/(?P<ods_code>\w+)$', MapOrganisationCoords.as_view(), name='org-coords-map'),
    url(r'^pick-provider$', OrganisationPickProvider.as_view(), name='org-pick-provider'),
    url(r'^summary$', Summary.as_view(), name='org-all-summary'),
    url(r'^summary/(?P<ods_code>\w+)$', OrganisationSummary.as_view(), name='public-org-summary'),
    url(r'^problems/(?P<ods_code>\w+)$', OrganisationProblems.as_view(), name='public-org-problems'),
    url('^/(?P<ods_code>\w+)$', OrganisationReviews.as_view(), name="public-org-reviews"),
    url(r'^search$', OrganisationSearch.as_view(), name='org-search'),
)
