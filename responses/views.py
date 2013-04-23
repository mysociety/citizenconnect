from django.views.generic import CreateView, TemplateView, FormView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from concurrency.exceptions import RecordModifiedError

from citizenconnect.shortcuts import render
from organisations.auth import enforce_response_access_check
from issues.models import Problem
from issues.lib import changes_for_model

from .forms import ProblemResponseForm
from issues.forms import LookupForm
from .models import ProblemResponse


class ResponseLookup(FormView):
    template_name = 'responses/response_lookup.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        context = RequestContext(self.request)
        response_url = reverse("response-form", kwargs={'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(response_url)


class ResponseForm(CreateView):

    template_name = 'responses/response-form.html'
    confirm_template = 'responses/response-confirm.html'
    model = ProblemResponse
    form_class = ProblemResponseForm

    def get_form_kwargs(self):
        # Add the request to the form's kwargs
        kwargs = super(ResponseForm, self).get_form_kwargs()
        kwargs.update({
            'request' : self.request
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(ResponseForm, self).get_context_data(**kwargs)
        context['issue'] = self.issue
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
        enforce_response_access_check(self.issue, self.request.user)
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
            # Because we haven't necessarily called form.save(), manually
            # unset the session-based issue version tracker too
            form.unset_version_in_session()

        return render(self.request, self.confirm_template, context)
