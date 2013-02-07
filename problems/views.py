# Django imports
from django.views.generic import FormView, TemplateView, CreateView
from django.core.urlresolvers import reverse
from django.template import RequestContext

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList, OrganisationAwareViewMixin

from .forms import ProblemForm
from .models import Problem

class PickProvider(FormView):
    template_name = 'problems/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'problems/provider-results.html'

class ProblemCreate(CreateView, OrganisationAwareViewMixin):
    model = Problem
    form_class = ProblemForm

    def get_success_url(self):
        # Get the request context (ie: run our context processors)
        # So that we know what cobrand to use
        context = RequestContext(self.request)
        return reverse('problem-confirm', kwargs={'cobrand':context.get("cobrand").get("name")})

    def get_initial(self):
        initial = super(ProblemCreate, self).get_initial()
        initial = initial.copy()
        # TODO - get the organisation, can we get it from the context?
        return initial

class ProblemConfirm(TemplateView):
    template_name = 'problems/problem-confirm.html'

class ProblemPublicView(TemplateView):
    template_name = 'problems/public.html'
