# Django imports
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.core.urlresolvers import reverse

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from questions.models import Question
from problems.models import Problem

class Home(TemplateView):
    template_name = 'index.html'

class CobrandChoice(TemplateView):
    template_name = 'cobrand_choice.html'

class About(TemplateView):
    template_name = 'about.html'

class MessageCreateViewMixin(object):

    def get_success_url(self):
        # Get the request context (ie: run our context processors)
        # So that we know what cobrand to use
        context = RequestContext(self.request)
        return reverse(self.confirm_url, kwargs={'cobrand':context["cobrand"]["name"]})

    def get_initial(self):
        initial = super(MessageCreateViewMixin, self).get_initial()
        initial = initial.copy()
        self.organisation = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        initial['organisation'] = self.organisation
        return initial

    def get_form(self, form_class):
        form = super(MessageCreateViewMixin, self).get_form(form_class)
        services = Service.objects.filter(organisation=self.organisation).order_by('name')
        if len(services) == 0:
            form.fields['service'].widget = HiddenInput()
        else:
            form.fields['service'].queryset = services
        return form

class PrivateMessageEditViewMixin(object):
    """
    Mixin for views which need to edit/update a message object on private urls.

    Deals with some of the common functionality to save repeating yourself.

    Three class attributes you should provide in your class:

    confirm_url - The url name to redirect successful form submissions to
    question_form - The form class to use for Question models
    problem_form - The form class to use for Problem models
    """

    # Standardise the context_object's name
    context_object_name = 'message'

    def get_success_url(self):
        """
        Return a confirmation url for the form to redirect to.
        """
        return reverse(self.confirm_url)

    def get_form_class(self):
        """
        Return the right form class depending on what model we're editing.
        """
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            return self.question_form
        elif message_type == 'problem':
            return self.problem_form
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
            return Question.objects.all()
        elif message_type == 'problem':
            return Problem.objects.all()
        else:
            raise ValueError("Unknown message type: %s" % message_type)
