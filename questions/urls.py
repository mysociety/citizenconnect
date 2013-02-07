from django.conf.urls import patterns, include, url

from .views import *

urlpatterns = patterns('',
    url(r'^ask-question$', AskQuestion.as_view(), name='ask-question'),
    url(r'^pick-provider$', PickProvider.as_view(), name='questions-pick-provider'),
    url(r'^provider-results$', ProviderResults.as_view(), name='questions-provider-results'),
    url(r'^question-form/(?P<organisation_type>\w+)/(?P<choices_id>\d+)$', QuestionForm.as_view(), name='question-form'),
    url(r'^question-confirm$', QuestionConfirm.as_view(), name='question-confirm'),
    url(r'^(?P<question_id>\d+)$', QuestionPublicView.as_view(), name='question-view')
)


