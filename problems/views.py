# Django imports
from django.views.generic import TemplateView, CreateView, DetailView

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase, OrganisationAwareViewMixin
from citizenconnect.views import MessageCreateViewMixin

from .forms import ProblemForm
from .models import Problem

class PickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'

class ProblemCreate(OrganisationAwareViewMixin, MessageCreateViewMixin, CreateView):
    model = Problem
    form_class = ProblemForm
    confirm_template = 'problems/problem-confirm.html'

class ProblemDetail(DetailView):
    model = Problem
