from django.views.generic import TemplateView, CreateView, DetailView, UpdateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.http import Http404

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from organisations.views.base import PickProviderBase
from organisations.views.organisations import OrganisationAwareViewMixin
from organisations.auth import enforce_problem_access_check
from organisations.lib import interval_counts

from .models import Problem
from .forms import ProblemForm, ProblemSurveyForm, ProblemImageInlineFormSet
from .lib import base32_to_int


class ProblemPickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'
    title_text = 'Report a Problem'


class ProblemCreate(OrganisationAwareViewMixin, CreateView):
    model = Problem
    form_class = ProblemForm
    confirm_template = 'issues/problem_confirm.html'

    def form_valid(self, form):
        # If we have images too, we have to check them manually for validity
        context = self.get_context_data()
        if 'image_forms' in context:
            image_forms = context['image_forms']
            if image_forms.is_valid():
                self.object = form.save()
                image_forms.instance = self.object
                image_forms.save()
            else:
                # An error
                return self.render_to_response(self.get_context_data(form=form))
        else:
            # No images, just a problem
            self.object = form.save()

        # Set the cobrand on the problem so we can use it for the survey later
        context = RequestContext(self.request)
        self.object.cobrand = context['cobrand']['name']
        self.object.save()
        context['object'] = self.object
        context['summary'] = interval_counts(organisation_filters={'organisation_id': self.object.organisation.id})
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
            form.fields['service'].empty_label = "Select service"
        return form

    def get_context_data(self, **kwargs):
        context = super(ProblemCreate, self).get_context_data(**kwargs)
        context['CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION'] = Problem.CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION
        if self.request.POST:
            context['image_forms'] = ProblemImageInlineFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object
            )
        else:
            context['image_forms'] = ProblemImageInlineFormSet(instance=self.object)

        return context


class ProblemDetail(DetailView):

    model = Problem

    def get_object(self, *args, **kwargs):
        obj = super(ProblemDetail, self).get_object(*args, **kwargs)
        enforce_problem_access_check(obj, self.request.user)
        return obj


class ProblemSurvey(UpdateView):
    model = Problem
    form_class = ProblemSurveyForm
    template_name = 'issues/problem_survey_form.html'
    confirm_template = 'issues/problem_survey_confirm.html'

    def get_object(self):
        id = self.kwargs.get('id', None)
        try:
            id = base32_to_int(id)
        except ValueError:
            raise Http404

        problem = get_object_or_404(Problem, id=id)
        # Record the first survey response
        response = self.kwargs.get('response', None)
        if response == 'y':
            problem.happy_service = True
        elif response == 'n':
            problem.happy_service = False
        problem.save()
        return problem

    def form_valid(self, form):
        self.object = form.save()
        context = RequestContext(self.request)
        context['object'] = self.object
        return render(self.request, self.confirm_template, context)


class CommonQuestions(TemplateView):
    template_name = 'issues/common_questions.html'
