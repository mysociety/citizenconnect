from django.views.generic import CreateView, TemplateView
from django.core.urlresolvers import reverse

from problems.models import Problem
from questions.models import Question

from .forms import QuestionResponseForm, ProblemResponseForm
from .models import ProblemResponse, QuestionResponse

class ResponseForm(CreateView):

    template_name = 'responses/response-form.html'

    def get_success_url(self):
        return reverse('response-confirm')

    def get_form_class(self):
        """
        Return the right form class depending on what model we're editing.
        """
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            return QuestionResponseForm
        elif message_type == 'problem':
            return ProblemResponseForm
        else:
            raise ValueError("Unknown message type: %s" % message_type)

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
        print initial
        return initial

    def get_context_data(self, form):
        context = super(ResponseForm, self).get_context_data()
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            context['message'] = Question.objects.get(pk=self.kwargs['pk'])
        elif message_type == 'problem':
            context['message'] = Problem.objects.get(pk=self.kwargs['pk'])
        else:
            raise ValueError("Unknown message type: %s" % message_type)
        return context

    def get_queryset(self):
        """
        Determine the queryset dynamically based on the message_type.
        This is another way of specifying the Model we're editing, but there isn't
        a get_model method to use for that, so we do this instead.
        """
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            return QuestionResponse.objects.all()
        elif message_type == 'problem':
            return ProblemResponse.objects.all()
        else:
            raise ValueError("Unknown message type: %s" % message_type)

class ResponseConfirm(TemplateView):
    template_name = 'responses/response-confirm.html'