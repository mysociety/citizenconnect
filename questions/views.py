# Django imports
from django.views.generic import TemplateView, CreateView, DetailView

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase, OrganisationAwareViewMixin
from citizenconnect.views import MessageCreateViewMixin

from .models import Question
from .forms import QuestionForm

class AskQuestion(TemplateView):
    template_name = 'questions/ask-question.html'

class PickProvider(PickProviderBase):
    result_link_url_name = 'question-form'

class QuestionCreate(OrganisationAwareViewMixin, MessageCreateViewMixin, CreateView):
    model = Question
    form_class = QuestionForm
    confirm_url = 'question-confirm'

class QuestionConfirm(TemplateView):
    template_name = 'questions/question-confirm.html'

class QuestionDetail(DetailView):
    model = Question
