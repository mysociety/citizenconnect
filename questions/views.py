
# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList, OrganisationAwareViewMixin

class AskQuestion(TemplateView):
    template_name = 'questions/ask-question.html'

class PickProvider(FormView):
    template_name = 'questions/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'questions/provider-results.html'

class QuestionForm(TemplateView, OrganisationAwareViewMixin):
    template_name = 'questions/question-form.html'

class QuestionConfirm(TemplateView):
    template_name = 'questions/question-confirm.html'

class QuestionPublicView(TemplateView):
    template_name = 'questions/public.html'
