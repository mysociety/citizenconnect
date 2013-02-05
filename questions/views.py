
# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList, OrganisationFormView

def ask_question(request):
    return render(request, 'ask-question.html')

class PickProvider(FormView):
    template_name = 'pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'provider-results.html'

class QuestionForm(OrganisationFormView):
    template_name = 'question-form.html'

def question_confirm(request):
    return render(request, 'question-confirm.html')
