from django.views.generic import CreateView, TemplateView
from django.core.urlresolvers import reverse
from django.template import RequestContext

from citizenconnect.shortcuts import render
from organisations.auth import check_problem_access
from issues.models import Problem

from .forms import ProblemResponseForm
from .models import ProblemResponse

class ResponseForm(CreateView):

    template_name = 'responses/response-form.html'
    confirm_template = 'responses/response-confirm.html'
    model = ProblemResponse
    form_class = ProblemResponseForm
    initial_object_name = 'message'

    def get_context_data(self, **kwargs):
        context = super(ResponseForm, self).get_context_data(**kwargs)
        context['message'] = Problem.objects.get(pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('response-confirm')

    def get_initial(self):
        initial = super(ResponseForm, self).get_initial()
        message = Problem.objects.get(pk=self.kwargs['pk'])
        initial['message'] = message
        initial['message_status'] = message.status
        # Check that the user has access to message before allowing them to respond
        check_problem_access(message, self.request.user)
        return initial

    def form_valid(self, form):
        context = RequestContext(self.request)

        # Only save the response at all if it's not empty
        if 'response' in form.cleaned_data and form.cleaned_data['response']:
            self.object = form.save()
            context['response'] = self.object

        # Process the message status field to actually change the message's
        # status, because this form is a CreateView for a ProblemResponse
        # so will just ignore that field normally.
        if 'message_status' in form.cleaned_data and form.cleaned_data['message_status']:
            message = form.cleaned_data['message']
            message.status = form.cleaned_data['message_status']
            message.save()
            context['message'] = message

        return render(self.request, self.confirm_template, context)
