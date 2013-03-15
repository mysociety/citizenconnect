from django.views.generic import TemplateView, CreateView, DetailView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.core.exceptions import PermissionDenied

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from organisations.views import PickProviderBase, OrganisationAwareViewMixin

from .models import Question, Problem
from .forms import QuestionForm, ProblemForm

def _check_message_access(message, user):
    if not message.can_be_accessed_by(user):
        raise PermissionDenied()

class AskQuestion(TemplateView):
    template_name = 'issues/ask-question.html'

class QuestionCreate(CreateView):
    model = Question
    form_class = QuestionForm
    confirm_template = 'issues/question-confirm.html'

    def form_valid(self, form):
        self.object = form.save()
        context = RequestContext(self.request)
        context['object'] = self.object
        return render(self.request, self.confirm_template, context)

class ProblemPickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'

class ProblemCreate(OrganisationAwareViewMixin, CreateView):
    model = Problem
    form_class = ProblemForm
    confirm_template = 'issues/problem-confirm.html'

    def form_valid(self, form):
        self.object = form.save()
        context = RequestContext(self.request)
        context['object'] = self.object
        return render(self.request, self.confirm_template, context)

    def get_initial(self):
        initial = super(ProblemCreate, self).get_initial()
        initial = initial.copy()
        self.organisation = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        initial['organisation'] = self.organisation
        return initial

    def get_form(self, form_class):
        form = super(ProblemCreate, self).get_form(form_class)
        services = Service.objects.filter(organisation=self.organisation).order_by('name')
        if len(services) == 0:
            form.fields['service'].widget = HiddenInput()
        else:
            form.fields['service'].queryset = services
            form.fields['service'].empty_label = "None"
        return form

class ProblemDetail(DetailView):

    model = Problem

    def get_object(self, *args, **kwargs):
        obj = super(ProblemDetail, self).get_object(*args, **kwargs)
        _check_message_access(obj, self.request.user)
        return obj
