from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^pick-provider$', ReviewPickProvider.as_view(), name='reviews-pick-provider'),
    url(r'^review-form/(?P<ods_code>\w+)$', ReviewForm.as_view(), name='review-form'),
    url(r'^review-confirm/(?P<ods_code>\w+)$', ReviewConfirm.as_view(), name='review-confirm'),
)
