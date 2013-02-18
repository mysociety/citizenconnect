from django.conf.urls import patterns, include, url

from .views import APIProblemCreate, APIQuestionCreate

urlpatterns = patterns('',
    url(r'^problem$', APIProblemCreate.as_view(), name='api-problem-create'),
    url(r'^question$', APIQuestionCreate.as_view(), name='api-question-create')
)
