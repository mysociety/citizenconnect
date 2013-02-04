from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^ask-question$', 'questions.views.ask_question', name='ask-question'),
    url(r'^pick-provider$', 'questions.views.pick_provider', name='pick-provider'),
    url(r'^provider-results$', 'questions.views.provider_results', name='provider-results'),
    url(r'^question-form$', 'questions.views.question_form', name='question-form'),
    url(r'^question-confirm$', 'questions.views.question_confirm', name='question-confirm'),
)


