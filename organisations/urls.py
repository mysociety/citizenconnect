from django.conf.urls import patterns, url

from .views import *

urlpatterns = patterns('',
    url(r'^demo_finder$', OrganisationFinderDemo.as_view(), name='org-finder-demo'),
    url(r'^list$', OrganisationList.as_view(), name='org-list'),
)