from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^dashboard/(?P<ods_code>\w+)$', OrganisationDashboard.as_view(), name='org-dashboard'),
    url(r'^response/(?P<message_type>question|problem)/(?P<pk>\d+)$', ResponseForm.as_view(), name='org-response-form'),
    url(r'^response-confirm$', ResponseConfirm.as_view(), name='org-response-confirm'),
    url(r'^summary/(?P<ods_code>\w+)$',
            OrganisationSummary.as_view(),
            name='private-org-summary',
            kwargs={'private': True}),

)
