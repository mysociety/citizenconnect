from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^dashboard/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', OrganisationDashboard.as_view(), name='org-dashboard'),
    url(r'^response/(?P<message_type>question|problem)/(?P<pk>\d+)$', ResponseForm.as_view(), name='org-response-form'),
    url(r'^response-confirm$', ResponseConfirm.as_view(), name='org-response-confirm'),
    url(r'^summary/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$',
            OrganisationSummary.as_view(),
            name='private-org-summary',
            kwargs={'private': True}),

)
