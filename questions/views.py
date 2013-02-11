# Django imports
from django.views.generic import FormView, TemplateView, CreateView, DetailView
from django.core.urlresolvers import reverse
from django.template import RequestContext

# App imports
from citizenconnect.shortcuts import render
from organisations.forms import OrganisationFinderForm
from organisations.views import OrganisationList, OrganisationAwareViewMixin

from .models import Question
from .forms import QuestionForm

class AskQuestion(TemplateView):
    template_name = 'questions/ask-question.html'

class PickProvider(FormView):
    template_name = 'questions/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'questions/provider-results.html'

class QuestionCreate(OrganisationAwareViewMixin, CreateView):
    model = Question
    form_class = QuestionForm

    def get_success_url(self):
        # Get the request context (ie: run our context processors)
        # So that we know what cobrand to use
        context = RequestContext(self.request)
        return reverse('question-confirm', kwargs={'cobrand':context["cobrand"]["name"]})

    def get_initial(self):
        initial = super(QuestionCreate, self).get_initial()
        initial = initial.copy()
        initial['organisation_type'] = self.kwargs['organisation_type']
        initial['choices_id'] = self.kwargs['choices_id']
        return initial

class QuestionConfirm(TemplateView):
    template_name = 'questions/question-confirm.html'

class QuestionDetail(DetailView):
    model = Question
