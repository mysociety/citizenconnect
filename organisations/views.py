# Standard imports
from ukpostcodeutils import validation
import re

# Django imports
from django.views.generic import FormView, TemplateView

# App imports
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

        context['location'] = location
        postcode = re.sub('\s+', '', location.upper())
        if validation.is_valid_postcode(postcode):
            api = ChoicesAPI()
            organisations = api.hospitals_by_postcode(postcode)
            context['organisations'] = organisations
        return context