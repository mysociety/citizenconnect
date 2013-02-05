from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns('',
    url(r'^demo_finder$', OrganisationFinderDemo.as_view(), name='org-finder-demo'),
    url(r'^list$', OrganisationList.as_view(), name='org-list'),
    url(r'^map$', 'organisations.views.map', name='org-map'),
    url(r'^pick-provider$', PickProvider.as_view(), name='org-pick-provider'),
    url(r'^provider-results$', ProviderResults.as_view(), name='org-provider-results'),
    url(r'^summary$', Summary.as_view(), name='org-all-summary'),
    url(r'^summary/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', OrganisationSummary.as_view(), name='org-summary'),
    url(r'^dashboard/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', OrganisationDashboard.as_view(), name='org-dashboard'),
    url(r'^response$', ResponseForm.as_view(), name='org-response-form'),
    url(r'^response-confirm$', ResponseConfirm.as_view(), name='org-response-confirm'),
)