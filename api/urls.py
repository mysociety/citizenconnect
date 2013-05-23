from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

from .views import APIProblemCreate
from .middleware import basic_auth

urlpatterns = patterns('',
    url(r'^problem$', basic_auth(csrf_exempt(APIProblemCreate.as_view())), name='api-problem-create'),
)
