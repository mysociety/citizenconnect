from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from .views import ModerateHome, ModerateLookup, ModerateForm, ModerateConfirm

urlpatterns = patterns('',
    url(r'^$', login_required(ModerateHome.as_view()), name='moderate-home'),
    url(r'^lookup$', login_required(ModerateLookup.as_view()), name='moderate-lookup'),
    url(r'^(?P<message_type>question|problem)/(?P<pk>\d+)$', login_required(ModerateForm.as_view()), name='moderate-form'),
    url(r'^confirm$', login_required(ModerateConfirm.as_view()), name='moderate-confirm')
)
