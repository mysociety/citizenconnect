from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import *

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)$', login_required(ResponseForm.as_view()), name='response-form'),
    url(r'^lookup$', login_required(ResponseLookup.as_view()), name='response-lookup'),
)
