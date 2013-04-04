from django.views.generic import CreateView, TemplateView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import get_object_or_404

from concurrency.exceptions import RecordModifiedError

from citizenconnect.shortcuts import render
from organisations.auth import check_problem_access
from issues.models import Problem
from issues.lib import changes_for_model

from .forms import ProblemResponseForm
from .models import ProblemResponse

class ResponseForm(CreateView):

    template_name = 'responses/response-form.html'
    confirm_template = 'responses/response-confirm.html'
    model = ProblemResponse
    form_class = ProblemResponseForm

    def set_issue_version_in_session(self):
        # Save the issue version in the user's session
        self.request.session.setdefault('problem_versions', {})
        self.request.session['problem_versions'][self.issue.id] = self.issue.version
        # We need to do this because we haven't modified request.session itself
        self.request.session.modified = True

    def unset_issue_version_in_session(self):
        # Save the issue version in the user's session
        if self.request.session.get('problem_versions', {}):
            if self.issue.id in self.request.session['problem_versions']:
                del self.request.session['problem_versions'][self.issue.id]
        # We need to do this because we haven't modified request.session itself
        self.request.session.modified = True

    def get(self, request, *args, **kwargs):
        response = super(ResponseForm, self).get(request, *args, **kwargs)
        self.request = request
        self.set_issue_version_in_session()
        return response

    def get_form_kwargs(self):
        # Add the request to the form's kwargs
        kwargs = super(ResponseForm, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ResponseForm, self).get_context_data(**kwargs)
        context['issue'] = Problem.objects.get(pk=self.kwargs['pk'])
        context['history'] = changes_for_model(context['issue'])
        return context

    def get_success_url(self):
        return reverse('response-confirm')

    def get_initial(self):
        initial = super(ResponseForm, self).get_initial()
        self.issue = get_object_or_404(Problem, pk=self.kwargs['pk'])
        initial['issue'] = self.issue
        initial['issue_status'] = self.issue.status
        # Check that the user has access to issue before allowing them to respond
        check_problem_access(self.issue, self.request.user)
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

        # Unset the session-based issue version tracker
        self.unset_issue_version_in_session()

        return render(self.request, self.confirm_template, context)
