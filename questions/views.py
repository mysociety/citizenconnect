
# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList

def ask_question(request):
    return render(request, 'questions/ask-question.html')

class PickProvider(FormView):
    template_name = 'questions/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'questions/provider-results.html'

class QuestionForm(TemplateView):
    template_name = 'questions/question-form.html'
    choices_id = None
    org_type = None

def question_confirm(request):
    return render(request, 'questions/question-confirm.html')
