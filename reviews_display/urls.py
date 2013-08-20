from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns(
    '',
    url('^/(?P<ods_code>\w+)/(?P<api_posting_id>\w+)$', ReviewDetail.as_view(), name="review-detail"),
)
