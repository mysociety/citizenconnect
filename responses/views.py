from django.views.generic import CreateView, TemplateView
from django.core.urlresolvers import reverse
from django.template import RequestContext

from citizenconnect.shortcuts import render
from issues.views import MessageAwareViewMixin, MessageDependentFormViewMixin
from issues.models import Problem, Question

from .forms import QuestionResponseForm, ProblemResponseForm
from .models import ProblemResponse, QuestionResponse

class ResponseForm(MessageAwareViewMixin,
                   MessageDependentFormViewMixin,
                   CreateView):

    template_name = 'responses/response-form.html'
    confirm_template = 'responses/response-confirm.html'

    # Parameters for MessageDependentFormViewMixin
    problem_form_class = ProblemResponseForm
    question_form_class = QuestionResponseForm
    problem_queryset = ProblemResponse.objects.all()
    question_queryset = QuestionResponse.objects.all()
    # Put some initial data in the 'message' variable
    initial_object_name = 'message'

    def get_success_url(self):
        return reverse('response-confirm')

    def get_initial(self):
        initial = super(ResponseForm, self).get_initial()
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            message = Question.objects.get(pk=self.kwargs['pk'])
            initial['message'] = message
            initial['message_status'] = message.status
        elif message_type == 'problem':
            message = Problem.objects.get(pk=self.kwargs['pk'])
            initial['message'] = message
            initial['message_status'] = message.status
        else:
            raise ValueError("Unknown message type: %s" % message_type)
        return initial

    def form_valid(self, form):
        # Process the message status field to actually change the message's
        # status, because this form is a CreateView for a ProblemResponse
        # or QuestionResponse, so will just ignore that field normally.
        self.object = form.save()

        if 'message_status' in form.cleaned_data and form.cleaned_data['message_status']:
            message = self.object.message
            message.status = form.cleaned_data['message_status']
            message.save()

        # Show the confirmation page, and give it the response object to use
        context = RequestContext(self.request)
        context['response'] = self.object
        return render(self.request, self.confirm_template, context)