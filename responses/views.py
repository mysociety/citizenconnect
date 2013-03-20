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
    initial_object_name = 'issue'

    def get_context_data(self, **kwargs):
        context = super(ResponseForm, self).get_context_data(**kwargs)
        context['issue'] = Problem.objects.get(pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse('response-confirm')

    def get_initial(self):
        initial = super(ResponseForm, self).get_initial()
        issue = Problem.objects.get(pk=self.kwargs['pk'])
        initial['issue'] = issue
        initial['issue_status'] = issue.status
        # Check that the user has access to issue before allowing them to respond
        check_problem_access(issue, self.request.user)
        return initial

    def form_valid(self, form):
        context = RequestContext(self.request)

        # Only save the response at all if it's not empty
        if 'response' in form.cleaned_data and form.cleaned_data['response']:
            self.object = form.save()
            context['response'] = self.object

        # Process the issue status field to actually change the issue's
        # status, because this form is a CreateView for a ProblemResponse
        # so will just ignore that field normally.
        if 'issue_status' in form.cleaned_data and form.cleaned_data['issue_status']:
            issue = form.cleaned_data['issue']
            issue.status = form.cleaned_data['issue_status']
            issue.save()
            context['issue'] = issue

        return render(self.request, self.confirm_template, context)
