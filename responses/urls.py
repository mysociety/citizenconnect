from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns('',
    url(r'^(?P<message_type>question|problem)/(?P<pk>\d+)$', ResponseForm.as_view(), name='response-form'),
    url(r'^confirm$', ResponseConfirm.as_view(), name='response-confirm'),
)
