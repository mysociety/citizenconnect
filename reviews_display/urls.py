from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url('^/(?P<ods_code>\w+)$', ReviewOrganisationList.as_view(), name="review-organisation-list"),
    url('^/(?P<ods_code>\w+)/(?P<pk>\w+)$', ReviewDetail.as_view(), name="review-detail"),
)
