# Standard imports
from itertools import chain
from operator import attrgetter
import json

# Django imports
from django.views.generic import FormView, TemplateView, UpdateView, ListView
from django.template.defaultfilters import escape
from django.core.urlresolvers import reverse
from django.template import RequestContext

# App imports
from citizenconnect.shortcuts import render
from citizenconnect.views import PrivateMessageEditViewMixin
from problems.models import Problem
from questions.models import Question

from .models import Organisation
from .forms import OrganisationFinderForm, QuestionResponseForm, ProblemResponseForm
import choices_api
from .lib import interval_counts
from .models import Organisation

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
        problems = organisation.problem_set.all()
        questions = organisation.question_set.all()
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

        # TODO - should be able to serialize the organisations list directly
        # but that'll need some jiggling with the serializers to get the
        # open issues in too
        organisations_list = []
        for organisation in organisations:
            organisation_dict = {}
            organisation_dict['ods_code'] = organisation.ods_code
            organisation_dict['name'] = organisation.name
            organisation_dict['lon'] = organisation.point.coords[0]
            organisation_dict['lat'] = organisation.point.coords[1]
            if organisation.organisation_type == 'gppractices':
                organisation_dict['type'] = "GP"
            elif organisation.organisation_type == 'hospitals':
                organisation_dict['type'] = "Hospital"
            else :
                organisation_dict['type'] = "Unknown"
            organisation_dict['issues'] = []
            for issue in organisation.open_issues:
                organisation_dict['issues'].append(escape(issue.description))
            organisations_list.append(organisation_dict)

        # Make it into a JSON string
        context['organisations'] = json.dumps(organisations_list)

        return context

class PickProviderBase(ListView):
    template_name = 'provider-results.html'
    form_template_name = 'pick-provider.html'
    result_link_url_name = 'public-org-summary'
    paginate_by = 10
    model = Organisation
    context_object_name = 'organisations'

    def get(self, *args, **kwargs):
        super(PickProviderBase, self).get(*args, **kwargs)
        if self.request.GET:
            form = OrganisationFinderForm(self.request.GET)
            if form.is_valid(): # All validation rules pass
                context = {'location': form.cleaned_data['location'],
                           'organisation_type': form.cleaned_data['organisation_type'],
                           'organisations': form.cleaned_data['organisations'],
                           'result_link_url_name': self.result_link_url_name,
                           'paginator': None,
                           'page_obj': None,
                           'is_paginated': False}
                self.queryset = form.cleaned_data['organisations']
                page_size = self.get_paginate_by(self.queryset)
                if page_size:
                    paginator, page, queryset, is_paginated = self.paginate_queryset(self.queryset, page_size)
                    context['paginator'] = paginator
                    context['page_obj'] = page
                    context['is_paginated'] = is_paginated
                    context['organisations'] = queryset
                return render(self.request, self.template_name, context)
            else:
                return render(self.request, self.form_template_name, {'form': form})
        else:
              return render(self.request, self.form_template_name, {'form': OrganisationFinderForm()})

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

    def get_context_data(self, **kwargs):
        context = super(Summary, self).get_context_data(**kwargs)
        context['gppractices'] = Organisation.objects.filter(organisation_type='gppractices')
        context['hospitals'] = Organisation.objects.filter(organisation_type='hospitals')
        context['problems_categories'] = Problem.CATEGORY_CHOICES
        context['questions_categories'] = Question.CATEGORY_CHOICES
        return context

class OrganisationDashboard(OrganisationAwareViewMixin,
                            OrganisationIssuesAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'

class ResponseForm(PrivateMessageEditViewMixin,
                   UpdateView):

    template_name = 'organisations/response-form.html'
    confirm_url = 'org-response-confirm'
    question_form_class = QuestionResponseForm
    problem_form_class = ProblemResponseForm

class ResponseConfirm(TemplateView):
    template_name = 'organisations/response-confirm.html'
