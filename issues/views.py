from django.conf import settings
from django.views.generic import TemplateView, DetailView, UpdateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.http import Http404

from django_tables2 import RequestConfig
from extra_views import CreateWithInlinesView, InlineFormSet, NamedFormsetsMixin

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from organisations.views.base import PickProviderBase, FilterFormMixin
from organisations.views.organisations import OrganisationAwareViewMixin
from organisations.views.organisation_parents import OrganisationParentAwareViewMixin
from organisations.auth import enforce_problem_access_check
from organisations.lib import interval_counts
from organisations.forms import OrganisationFilterForm

from .models import Problem, ProblemImage
from .forms import ProblemForm, ProblemSurveyForm
from .lib import base32_to_int
from .tables import (
    ProblemTable,
    ExtendedProblemTable,
    OrganisationParentProblemTable,
    BreachTable
)


class ProblemPickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'
    title_text = 'Report a Problem'
    # Limit the organisations the search will search in to active
    # organisations only
    queryset = Organisation.objects.active()


class ProblemImageInline(InlineFormSet):
    model = ProblemImage
    can_delete = False

    def get_factory_kwargs(self):
        """
        Overriden get_factory_kwargs to set `extra` and `max_num` from settings
        at runtime rather than as class properties, to make testing with overriden
        settings easier
        """
        kwargs = super(ProblemImageInline, self).get_factory_kwargs()
        kwargs['extra'] = settings.MAX_IMAGES_PER_PROBLEM
        kwargs['max_num'] = settings.MAX_IMAGES_PER_PROBLEM
        return kwargs


class ProblemCreate(OrganisationAwareViewMixin,
                    NamedFormsetsMixin,
                    CreateWithInlinesView):
    model = Problem
    form_class = ProblemForm
    confirm_template = 'issues/problem_confirm.html'
    context_object_name = 'problem'

    # Settings for the inline formsets
    inlines = [ProblemImageInline]
    inlines_names = ['image_forms']

    def post(self, request, *args, **kwargs):
        return super(ProblemCreate, self).post(request, *args, **kwargs)

    def forms_valid(self, form, inlines):
        self.object = form.save()
        for formset in inlines:
            formset.save()

        # Set the cobrand on the problem so we can use it for the survey later
        context = RequestContext(self.request)
        self.object.cobrand = context['cobrand']['name']
        self.object.save()

        context['problem'] = self.object
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
        return context


class ProblemDetail(DetailView):

    model = Problem
    template_name = 'issues/problem_detail.html'
    context_object_name = 'problem'

    def get_object(self, *args, **kwargs):
        obj = super(ProblemDetail, self).get_object(*args, **kwargs)
        enforce_problem_access_check(obj, self.request.user)
        return obj


class ProblemSurvey(UpdateView):
    model = Problem
    form_class = ProblemSurveyForm
    template_name = 'issues/problem_survey_form.html'
    confirm_template = 'issues/problem_survey_confirm.html'
    context_object_name = 'problem'

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
            problem.happy_outcome = True
        elif response == 'n':
            problem.happy_outcome = False
        problem.save()
        return problem

    def form_valid(self, form):
        self.object = form.save()
        context = RequestContext(self.request)
        context['problem'] = self.object
        return render(self.request, self.confirm_template, context)


class OrganisationProblems(OrganisationAwareViewMixin,
                           FilterFormMixin,
                           TemplateView):
    template_name = 'issues/organisation_problems.html'

    form_class = OrganisationFilterForm

    def get_form_kwargs(self):
        kwargs = super(OrganisationProblems, self).get_form_kwargs()

        kwargs['organisation'] = self.organisation
        # Only show service_id if the organisation has services
        if not self.organisation.has_services():
            kwargs['with_service_id'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganisationProblems, self).get_context_data(**kwargs)

        # Get a queryset of issues and apply any filters to them
        problems = context['organisation'].problem_set.all_not_rejected_visible_problems()
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Build a table
        table_args = {
            'private': context['private'],
            'cobrand': kwargs['cobrand']
        }

        if context['organisation'].has_services() and context['organisation'].has_time_limits():
            problem_table = ExtendedProblemTable(filtered_problems, **table_args)
        else:
            problem_table = ProblemTable(filtered_problems, **table_args)

        RequestConfig(self.request, paginate={'per_page': 8}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context


class OrganisationParentProblems(OrganisationParentAwareViewMixin,
                                 FilterFormMixin,
                                 TemplateView):

    template_name = 'issues/organisation_parent_problems.html'

    def get_form_kwargs(self):
        kwargs = super(OrganisationParentProblems, self).get_form_kwargs()

        # Turn off the ccg filter and filter organisations to this organisation_parent
        kwargs['with_ccg'] = False
        kwargs['organisations'] = Organisation.objects.filter(parent=self.organisation_parent)

        # Turn off the organisation_type filter
        kwargs['with_organisation_type'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganisationParentProblems, self).get_context_data(**kwargs)

        # Get a queryset of issues and apply any filters to them
        problems = self.organisation_parent.problem_set.all()
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Build a table
        table_args = {'private': context['private']}
        problem_table = OrganisationParentProblemTable(filtered_problems, **table_args)

        RequestConfig(self.request, paginate={'per_page': 8}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context


class OrganisationParentBreaches(OrganisationParentAwareViewMixin,
                                 TemplateView):

    template_name = 'issues/organisation_parent_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        return super(OrganisationParentBreaches, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(OrganisationParentBreaches, self).get_context_data(**kwargs)
        problems = Problem.objects.open_problems().filter(breach=True, organisation__parent=context['organisation_parent'])

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        return context
