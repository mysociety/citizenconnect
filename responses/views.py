from django.views.generic import CreateView, FormView
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

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
        response_url = reverse("response-form", kwargs={'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(response_url)

    def get_context_data(self, **kwargs):
        context = super(ResponseLookup, self).get_context_data(**kwargs)
        context['private'] = True

        # Persist this so that we can display it in the form if there is something wrong.
        context['reference_number'] = self.request.POST.get('reference_number', '')

        return context


class ResponseForm(CreateView):

    template_name = 'responses/response-form.html'
    confirm_template = 'responses/response-confirm.html'
    model = ProblemResponse
    form_class = ProblemResponseForm

    def get_form_kwargs(self):
        # Add the request to the form's kwargs
        kwargs = super(ResponseForm, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
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
        initial['issue_formal_complaint'] = self.issue.formal_complaint
        # Check that the user has access to issue before allowing them to respond
        enforce_response_access_check(self.issue, self.request.user)
        return initial

    def form_valid(self, form):
        context = RequestContext(self.request)

        # Only save the response at all if it's not empty
        if form.cleaned_data.get('response'):
            self.object = form.save()
            context['response'] = self.object

        # Process the issue status and formal_complaint fields
        # to actually change the issue's status, because this form
        # is a CreateView for a ProblemResponse
        # so will just ignore that field normally.
        if form.cleaned_data.get('issue_status') or form.cleaned_data.get('issue_formal_complaint'):
            issue = form.cleaned_data['issue']

            if form.cleaned_data.get('issue_status'):
                issue.status = form.cleaned_data['issue_status']

            if form.cleaned_data.get('issue_formal_complaint'):
                issue.formal_complaint = form.cleaned_data['issue_formal_complaint']

            issue.save()
            context['issue'] = issue
            # Because we haven't necessarily called form.save(), manually
            # unset the session-based issue version tracker too
            form.unset_version_in_session()

        return render(self.request, self.confirm_template, context)
