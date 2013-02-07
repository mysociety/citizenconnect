# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList

class PickProvider(FormView):
    template_name = 'reviews/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'reviews/provider-results.html'

class ReviewForm(TemplateView):
    template_name = 'reviews/review-form.html'
    choices_id = None
    org_type = None

class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'
