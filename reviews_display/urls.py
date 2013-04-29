from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',

    url('^$',                               ReviewList.as_view(),              name="review-list"),
    url('^/(?P<ods_code>\w+)$',             ReviewOrganisationList.as_view(),  name="review-organisation-list"),
    url('^/(?P<ods_code>\w+)/(?P<pk>\w+)$', ReviewDetail.as_view(),            name="review-detail"),

)
