# Standard imports

# Django imports
from django.views.generic import FormView

# App imports
from .forms import OrganisationFinderForm

class OrganisationFinderDemo(FormView):
    template_name = 'organisations/finder_demo.html'
    form_class = OrganisationFinderForm
