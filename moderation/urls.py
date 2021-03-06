from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from .views import ModerateHome, ModerateLookup, ModerateForm, ModerateConfirm, SecondTierModerateHome, SecondTierModerateForm, SecondTierModerateConfirm

urlpatterns = patterns('',
    url(r'^$', login_required(ModerateHome.as_view()), name='moderate-home'),
    url(r'^tier_two$', login_required(SecondTierModerateHome.as_view()), name='second-tier-moderate-home'),
    url(r'^tier_two/(?P<pk>\d+)$', login_required(SecondTierModerateForm.as_view()), name='second-tier-moderate-form'),
    url(r'^tier_two/confirm$', login_required(SecondTierModerateConfirm.as_view()), name='second-tier-moderate-confirm'),
    url(r'^lookup$', login_required(ModerateLookup.as_view()), name='moderate-lookup'),
    url(r'^(?P<pk>\d+)$', login_required(ModerateForm.as_view()), name='moderate-form'),
    url(r'^confirm$', login_required(ModerateConfirm.as_view()), name='moderate-confirm')
)
