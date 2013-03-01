from django.conf.urls import patterns, url

from organisations.views import *

urlpatterns = patterns('',
    url(r'^dashboard/(?P<ods_code>\w+)$', OrganisationDashboard.as_view(), name='org-dashboard'),
    url(r'^summary/(?P<ods_code>\w+)$',
            OrganisationSummary.as_view(),
            name='private-org-summary',
            kwargs={'private': True}),
    url(r'^problems/(?P<ods_code>\w+)$',
            OrganisationProblems.as_view(),
            name='private-org-problems',
            kwargs={'private': True}),
    url(r'^questions/(?P<ods_code>\w+)$',
            OrganisationQuestions.as_view(),
            name='private-org-questions',
            kwargs={'private': True}),
    url(r'^reviews/(?P<ods_code>\w+)$',
            OrganisationReviews.as_view(),
            name='private-org-reviews',
            kwargs={'private': True}),

    url(r'^map$', Map.as_view(), name='private-map', kwargs={'private': True}),

)
