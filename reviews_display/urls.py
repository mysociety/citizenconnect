from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',

    url('^$',                                      ReviewsOverview.as_view(),        name="reviews-overview"),
    # url('^/(?P<ods_code>\w+)$',                    ReviewsForOrganisation.as_view(), name="reviews-for-organisation"),
    # url('^/(?P<ods_code>\w+)/(?P<review_id>\w+)$', ReviewsDetail.as_view(),          name="reviews-detail"),

)
