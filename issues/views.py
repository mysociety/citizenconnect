from django.conf import settings
from django.views.generic import TemplateView, DetailView, UpdateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.http import Http404

from extra_views import CreateWithInlinesView, InlineFormSet, NamedFormsetsMixin

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service
from organisations.views.base import PickProviderBase
from organisations.views.organisations import OrganisationAwareViewMixin
from organisations.auth import enforce_problem_access_check
from organisations.lib import interval_counts

from .models import Problem, ProblemImage
from .forms import ProblemForm, ProblemSurveyForm
from .lib import base32_to_int


class ProblemPickProvider(PickProviderBase):
    result_link_url_name = 'problem-form'
    title_text = 'Report a Problem'


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
