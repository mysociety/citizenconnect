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

class MessageAwareViewMixin(object):
    """
    Mixin for views that are "aware" of a message, given via /problem/id or /question/id
    url parameters, and placed into a "message" context object for the template
    """

    def get_context_data(self, **kwargs):
        context = super(MessageAwareViewMixin, self).get_context_data(**kwargs)
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            context['message'] = Question.objects.get(pk=self.kwargs['pk'])
        elif message_type == 'problem':
            context['message'] = Problem.objects.get(pk=self.kwargs['pk'])
        else:
            raise ValueError("Unknown message type: %s" % message_type)
        return context

class MessageDependentFormViewMixin(object):
    """
    Mixin for form views which deal with either messages themselves or other objects,
    like responses to messages, which are basically the same but change some stuff
    based on whether the message is a Question or Problem.

    This works by dealing with the repetitive "is the message a problem or question"
    code in all the places where it would happen and the doing the right thing.

    To make it work you need to provide class attributes for each option:

    question_form_class - The form class to use when the message is a Question
    problem_form_class - The form class to use when the message is a Problem

    question_queryset - The queryset to use when the message is a Question
    problem_queryset - The queryset to use when the message is a Problem
    """

    def get_form_class(self):
        """
        Return the right form class depending on what model we're editing.
        """
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            return self.question_form_class
        elif message_type == 'problem':
            return self.problem_form_class
        else:
            raise ValueError("Unknown message type: %s" % message_type)

    def get_queryset(self):
        """
        Determine the queryset dynamically based on the message_type.
        This is another way of specifying the Model we're editing, but there isn't
        a get_model method to use for that, so we do this instead.
        """
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            return self.question_queryset
        elif message_type == 'problem':
            return self.problem_queryset
        else:
            raise ValueError("Unknown message type: %s" % message_type)

class MessageDetailViewMixin(DetailView):
    """
    Mixin for message detail views that checks access when getting the message
    object out
    """

    def get_object(self, *args, **kwargs):
        obj = super(MessageDetailViewMixin, self).get_object(*args, **kwargs)
        _check_message_access(obj, self.request.user)
        return obj

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

class QuestionDetail(DetailView):
    model = Question

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

class ProblemDetail(MessageDetailViewMixin):
    model = Problem
