from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^ask-question$', AskQuestion.as_view(), name='ask-question'),
    url(r'^pick-provider$', PickProvider.as_view(), name='questions-pick-provider'),
    url(r'^question-form/(?P<ods_code>\w+)$', QuestionCreate.as_view(), name='question-form'),
    url(r'^(?P<pk>\d+)$', QuestionDetail.as_view(), name='question-view')
)


