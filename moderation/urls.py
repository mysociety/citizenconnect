from django.conf.urls import patterns, include, url

from .views import ModerateHome, ModerateLookup, ModerateForm, ModerateConfirm

urlpatterns = patterns('',
    url(r'^$', ModerateHome.as_view(), name='moderate-home'),
    url(r'^lookup$', ModerateLookup.as_view(), name='moderate-lookup'),
    url(r'^(?P<message_type>question|problem)/(?P<pk>\d+)$', ModerateForm.as_view(), name='moderate-form'),
    url(r'^confirm$', ModerateConfirm.as_view(), name='moderate-confirm')
)
