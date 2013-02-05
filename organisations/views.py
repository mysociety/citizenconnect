# Standard imports
from ukpostcodeutils import validation
import re

# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from .forms import OrganisationFinderForm
from .choices_api import ChoicesAPI

class OrganisationFinderDemo(FormView):
    template_name = 'organisations/finder_demo.html'
    form_class = OrganisationFinderForm

class OrganisationList(TemplateView):
    template_name = 'organisations/list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationList, self).get_context_data(**kwargs)
        # Get the location GET parameter
        location = self.request.GET.get('location')
        organisation_type = self.request.GET.get('organisation_type')
        context['location'] = location
        api = ChoicesAPI()
        postcode = re.sub('\s+', '', location.upper())
        if validation.is_valid_postcode(postcode) or validation.is_valid_partial_postcode(postcode):
            search_type = 'postcode'
        else:
            search_type = 'name'
        organisations = api.find_organisations(search_type, location, organisation_type)
        context['organisations'] = organisations
        return context

class OrganisationFormView(TemplateView):

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationFormView, self).get_context_data(**kwargs)
        organisation_type = self.kwargs['organisation_type']
        choices_id = self.kwargs['choices_id']
        api = ChoicesAPI()
        context['organisation_name'] = api.get_organisation_name(organisation_type, choices_id)
        context['choices_id'] = choices_id
        context['organisation_type'] = organisation_type
        return context

def map(request):
    return render(request, 'organisations/map.html')

class PickProvider(FormView):
    template_name = 'organisations/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'organisations/provider-results.html'

class OrganisationSummary(TemplateView):
    template_name = 'organisations/organisation-summary.html'

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationSummary, self).get_context_data(**kwargs)
        organisation_type = self.kwargs['organisation_type']
        choices_id = self.kwargs['choices_id']
        api = ChoicesAPI()
        context['organisation_name'] = api.get_organisation_name(organisation_type, choices_id)
        context['choices_id'] = choices_id
        context['organisation_type'] = organisation_type
        return context

class Summary(TemplateView):
    template_name = 'organisations/summary.html'
