from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^dashboard/(?P<ods_code>\w+)$', OrganisationDashboard.as_view(), name='org-dashboard'),
    url(r'^summary/(?P<ods_code>\w+)$',
            OrganisationSummary.as_view(),
            name='private-org-summary',
            kwargs={'private': True}),

)
