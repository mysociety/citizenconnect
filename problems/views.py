# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList, OrganisationFormView

class PickProvider(FormView):
    template_name = 'problems/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'problems/provider-results.html'

class ProblemForm(OrganisationFormView):
    template_name = 'problems/problem-form.html'

def problem_confirm(request):
    return render(request, 'problems/problem-confirm.html')
