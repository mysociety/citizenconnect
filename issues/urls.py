from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^/question/ask-question$', AskQuestion.as_view(), name='ask-question'),
    url(r'^/question/pick-provider$', QuestionPickProvider.as_view(), name='questions-pick-provider'),
    url(r'^/question/question-form/(?P<ods_code>\w+)$', QuestionCreate.as_view(), name='question-form'),
    url(r'^/question/(?P<pk>\d+)$', QuestionDetail.as_view(), name='question-view'),

    url(r'^/problem/pick-provider$', ProblemPickProvider.as_view(), name='problems-pick-provider'),
    url(r'^/problem/problem-form/(?P<ods_code>\w+)$', ProblemCreate.as_view(), name='problem-form'),
    url(r'^/problem/(?P<pk>\d+)$', ProblemDetail.as_view(), name='problem-view')
)
