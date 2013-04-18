from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt

from .views import APIProblemCreate, APIQuestionCreate

urlpatterns = patterns('',
    url(r'^problem$', csrf_exempt(APIProblemCreate.as_view()), name='api-problem-create'),
)
