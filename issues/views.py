from django.views.generic import TemplateView, CreateView, DetailView, UpdateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from organisations.views import PickProviderBase, OrganisationAwareViewMixin, PrivateViewMixin
from organisations.auth import check_question_access, check_problem_access

from .models import Question, Problem
from .forms import QuestionForm, ProblemForm, QuestionUpdateForm

class AskQuestion(TemplateView):
    template_name = 'issues/ask_question.html'

class QuestionPickProvider(PickProviderBase):
    result_link_url_name = 'question-form'

class QuestionCreate(CreateView):
    model = Question
    form_class = QuestionForm
    confirm_template = 'issues/question_confirm.html'

    def form_valid(self, form):
        self.object = form.save()
        context = RequestContext(self.request)
        context['object'] = self.object
        return render(self.request, self.confirm_template, context)

    # Get the (optional) organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(QuestionCreate, self).get_context_data(**kwargs)
        if 'ods_code' in self.kwargs and self.kwargs['ods_code']:
            context['organisation'] = Organisation.objects.get(ods_code=self.kwargs['ods_code'])
        return context

    def get_initial(self):
        initial = super(QuestionCreate, self).get_initial()
        if 'ods_code' in self.kwargs and self.kwargs['ods_code']:
            initial = initial.copy()
            initial['organisation'] = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        return initial

class QuestionUpdate(PrivateViewMixin, UpdateView):
    model = Question
    form_class = QuestionUpdateForm
    context_object_name = "question"
    template_name = 'issues/question_update_form.html'
    confirm_template = 'issues/question_update_confirm.html'

    def dispatch(self, request, *args, **kwargs):
        check_question_access(request.user)
        return super(QuestionUpdate, self).dispatch(request, *args, **kwargs)

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
    confirm_template = 'issues/problem_confirm.html'

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
        check_problem_access(obj, self.request.user)
        return obj
