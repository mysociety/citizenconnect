# Django imports
from django.views.generic import FormView, TemplateView, CreateView, DetailView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import get_object_or_404

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase, OrganisationAwareViewMixin
from organisations.models import Organisation

from .models import Question
from .forms import QuestionForm

class AskQuestion(TemplateView):
    template_name = 'questions/ask-question.html'

class PickProvider(PickProviderBase):
    result_link_url_name = 'question-form'

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
        initial['organisation'] = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        return initial

class QuestionConfirm(TemplateView):
    template_name = 'questions/question-confirm.html'

class QuestionDetail(DetailView):
    model = Question
