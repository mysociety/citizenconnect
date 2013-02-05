from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^pick-provider$', PickProvider.as_view(), name='reviews-pick-provider'),
    url(r'^provider-results$', ProviderResults.as_view(), name='reviews-provider-results'),
    url(r'^review-form/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', ReviewForm.as_view(), name='review-form'),
    url(r'^review-confirm$', 'reviews.views.review_confirm', name='review-confirm'),
)


