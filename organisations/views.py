# Standard imports
from ukpostcodeutils import validation
from itertools import chain
from operator import attrgetter
import re
import json

# Django imports
from django.views.generic import FormView, TemplateView
from django.template.defaultfilters import escape

# App imports
from citizenconnect.shortcuts import render
from problems.models import Problem
from questions.models import Question

from .forms import OrganisationFinderForm
from .choices_api import ChoicesAPI
from .lib import interval_counts
from .models import Organisation

class OrganisationFinderDemo(FormView):
    template_name = 'organisations/finder_demo.html'
    form_class = OrganisationFinderForm

class OrganisationList(TemplateView):
    template_name = 'organisations/list.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationList, self).get_context_data(**kwargs)
        # Get the location GET parameter
        location = self.request.GET.get('location')
        organisation_type = self.request.GET.get('organisation_type')
        context['location'] = location
        api = ChoicesAPI()
        postcode = re.sub('\s+', '', location.upper())
        if validation.is_valid_postcode(postcode) or validation.is_valid_partial_postcode(postcode):
            search_type = 'postcode'
        else:
            search_type = 'name'
        organisations = api.find_organisations(organisation_type, search_type, location)
        context['organisations'] = organisations
        return context

class OrganisationAwareViewMixin(object):
    """Mixin class for views which need to have a reference to a particular
    organisation, such as problem and question forms."""

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        ods_code = self.kwargs['ods_code']
        context['organisation'] = Organisation.objects.get(ods_code=ods_code)
        return context

class OrganisationIssuesAwareViewMixin(object):
    """Mixin class for views which need to have reference to a particular organisation
    and the issues that belong to it, such as provider dashboards, and public provider
    pages"""

    def get_context_data(self, **kwargs):
        # Get all the problems and questions
        context = super(OrganisationIssuesAwareViewMixin, self).get_context_data(**kwargs)
        # Get the models related to this organisation, and let the db sort them
        ods_code = self.kwargs['ods_code']
        organisation = Organisation.objects.get(ods_code=ods_code)
        problems = organisation.problem_set
        questions = organisation.question_set
        context['organisation'] = organisation
        context['problems'] = problems
        context['questions'] = questions
        # Put them into one list, taken from http://stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view
        issues = sorted(
            chain(problems, questions),
            key=attrgetter('created'),
            reverse=True
        )
        context['issues'] = issues
        return context

class Map(TemplateView):
    template_name = 'organisations/map.html'

    def get_context_data(self, **kwargs):
        context = super(Map, self).get_context_data(**kwargs)

        # TODO - Filter by location
        organisations = Organisation.objects.all()

        # Make it into a JSON string
        context['organisations'] = json.dumps(list(organisations))

        return context

class PickProvider(FormView):
    template_name = 'organisations/pick-provider.html'
    form_class = OrganisationFinderForm

class ProviderResults(OrganisationList):
    template_name = 'organisations/provider-results.html'

class OrganisationSummary(OrganisationAwareViewMixin,
                          OrganisationIssuesAwareViewMixin,
                          TemplateView):
    template_name = 'organisations/organisation-summary.html'

    def get_context_data(self, **kwargs):
        context = super(OrganisationSummary, self).get_context_data(**kwargs)
        issue_types = {'problems': Problem,
                       'questions': Question}

        service = self.request.GET.get('service')
        if 'private' in kwargs and kwargs['private'] == True:
            context['private'] = True
        else:
            context['private'] = False
        # Use the filters we already have from OrganisationIssuesAwareViewMixin
        for issue_type, model_class in issue_types.items():
            category = self.request.GET.get('%s_category' % issue_type)
            if category in dict(model_class.CATEGORY_CHOICES):
                context['%s_category' % issue_type] = category
                context[issue_type] = context[issue_type].filter(category=category)
            context['%s_categories' % issue_type] = model_class.CATEGORY_CHOICES
            context['%s_total' % issue_type] = interval_counts(context[issue_type])
            status_list = []
            for status, description in model_class.STATUS_CHOICES:
                status_counts = interval_counts(context[issue_type].filter(status=status))
                status_counts['description'] = description
                status_list.append(status_counts)
            context['%s_by_status' % issue_type] = status_list

        return context

class Summary(TemplateView):
    template_name = 'organisations/summary.html'

class OrganisationDashboard(OrganisationAwareViewMixin,
                            OrganisationIssuesAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'

class ResponseForm(TemplateView):

    template_name = 'organisations/response-form.html'

    def get_context_data(self, **kwargs):
        context = super(ResponseForm, self).get_context_data(**kwargs)
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            context['message'] = Question.objects.get(id=self.kwargs['pk'])
        elif message_type == 'problem':
            context['message'] = Problem.objects.get(id=self.kwargs['pk'])
        else:
            raise ValueError("Unknown message type: %s" % message_type)
        return context

class ResponseConfirm(TemplateView):
    template_name = 'organisations/response-confirm.html'
