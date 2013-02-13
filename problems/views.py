# Django imports
from django.views.generic import FormView, TemplateView, CreateView, DetailView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import get_object_or_404

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase, OrganisationAwareViewMixin
from organisations.models import Organisation

from .forms import ProblemForm
from .models import Problem

class PickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'

class ProblemCreate(OrganisationAwareViewMixin, CreateView):
    model = Problem
    form_class = ProblemForm

    def get_success_url(self):
        # Get the request context (ie: run our context processors)
        # So that we know what cobrand to use
        context = RequestContext(self.request)
        return reverse('problem-confirm', kwargs={'cobrand':context["cobrand"]["name"]})

    def get_initial(self):
        initial = super(ProblemCreate, self).get_initial()
        initial = initial.copy()
        initial['organisation'] = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        return initial

class ProblemConfirm(TemplateView):
    template_name = 'problems/problem-confirm.html'

class ProblemDetail(DetailView):
    model = Problem
