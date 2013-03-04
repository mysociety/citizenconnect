# Standard imports
from itertools import chain
from operator import attrgetter
import json

# Django imports
from django.views.generic import FormView, TemplateView, UpdateView, ListView
from django.template.defaultfilters import escape
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django_tables2 import RequestConfig
from django.conf import settings

# App imports
from citizenconnect.shortcuts import render
from issues.models import Problem, Question

from .models import Organisation, Service
from .forms import OrganisationFinderForm
import choices_api
from .lib import interval_counts
from .models import Organisation
from .tables  import NationalSummaryTable, MessageModelTable, ExtendedMessageModelTable

class PrivateViewMixin(object):
    """
    Mixin for views which live at both /private urls and other
    urls, and need to know which is currently being requested.
    """

    def get_context_data(self, **kwargs):
        context = super(PrivateViewMixin, self).get_context_data(**kwargs)
        if 'private' in kwargs and kwargs['private'] == True:
            context['private'] = True
        else:
            context['private'] = False
        return context

class OrganisationAwareViewMixin(object):
    """Mixin class for views which need to have a reference to a particular
    organisation, such as problem and question forms."""

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation'] = Organisation.objects.get(ods_code=self.kwargs['ods_code'])
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

class MessageListMixin(PrivateViewMixin):
    """Mixin class for views which need to display a list of issues belonging to an organisation
       in either a public or private context"""

    def get_context_data(self, **kwargs):
        context = super(MessageListMixin, self).get_context_data(**kwargs)
        table_args = {'private': context['private'],
                      'message_type': self.message_type}
        if not context['private']:
            table_args['cobrand'] = kwargs['cobrand']
        organisation = Organisation.objects.get(ods_code=self.kwargs['ods_code'])
        if organisation.has_services() and organisation.has_time_limits():
            issue_table = ExtendedMessageModelTable(self.get_issues(organisation), **table_args)
        else:
            issue_table = MessageModelTable(self.get_issues(organisation), **table_args)
        context['organisation'] = organisation
        RequestConfig(self.request).configure(issue_table)
        context['issue_table'] = issue_table
        return context

class Map(PrivateViewMixin, TemplateView):
    template_name = 'organisations/map.html'

    def get_context_data(self, **kwargs):
        context = super(Map, self).get_context_data(**kwargs)

        # TODO - Filter by location
        organisations = Organisation.objects.all()

        # TODO - check the user has access to the map (ie: is a superuser)
        # when the user accounts work is merged in (after the expo)

        organisations_list = []
        for organisation in organisations:
            organisation_dict = {}
            organisation_dict['ods_code'] = organisation.ods_code
            organisation_dict['name'] = organisation.name
            organisation_dict['lon'] = organisation.point.coords[0]
            organisation_dict['lat'] = organisation.point.coords[1]

            # If we're showing the private map, link to the organisation's dashboard
            if context['private']:
                organisation_dict['url'] = reverse('org-dashboard', kwargs={'ods_code':organisation.ods_code})
            else :
                organisation_dict['url'] = reverse('public-org-summary', kwargs={'ods_code':organisation.ods_code, 'cobrand':kwargs['cobrand']})

            if organisation.organisation_type == 'gppractices':
                organisation_dict['type'] = "GP"
            elif organisation.organisation_type == 'hospitals':
                organisation_dict['type'] = "Hospital"
            else :
                organisation_dict['type'] = "Unknown"

            # TODO - use context['private'] to filter issues to public or private only
            # when we have that work merged in (after the expo)
            organisation_dict['problems'] = []
            for problem in organisation.problem_set.open_problems():
                organisation_dict['problems'].append(escape(problem.description))

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
                          TemplateView):
    template_name = 'organisations/organisation-summary.html'

    def get_context_data(self, **kwargs):
        context = super(OrganisationSummary, self).get_context_data(**kwargs)

        issue_types = {'problems': Problem,
                       'questions': Question}
        organisation = context['organisation']
        context['services'] = list(organisation.services.all().order_by('name'))
        selected_service = self.request.GET.get('service')
        if selected_service:
            if int(selected_service) in [ service.id for service in context['services'] ]:
                context['selected_service'] = int(selected_service)

        if 'private' in kwargs and kwargs['private'] == True:
            context['private'] = True
        else:
            context['private'] = False
        count_filters = {}
        # Use the filters we already have from OrganisationIssuesAwareViewMixin
        for issue_type, model_class in issue_types.items():
            if context.has_key('selected_service'):
                count_filters['service_id'] = selected_service
            category = self.request.GET.get('%s_category' % issue_type)
            if category in dict(model_class.CATEGORY_CHOICES):
                context['%s_category' % issue_type] = category
                count_filters['category'] = category
            context['%s_categories' % issue_type] = model_class.CATEGORY_CHOICES

            context['%s_total' % issue_type] = interval_counts(issue_type=issue_types[issue_type],
                                                               filters=count_filters,
                                                               organisation_id=organisation.id)
            status_list = []

            for status, description in model_class.STATUS_CHOICES:
                count_filters['status'] = status
                status_counts = interval_counts(issue_type=issue_types[issue_type],
                                                filters=count_filters,
                                                organisation_id=organisation.id)
                del count_filters['status']
                status_counts['description'] = description
                status_list.append(status_counts)
            context['%s_by_status' % issue_type] = status_list
        # Generate a dictionary of overall issue boolean counts to use in the summary
        # statistics
        issues_total = {}
        summary_attributes = ['happy_service',
                              'happy_outcome',
                              'acknowledged_in_time',
                              'addressed_in_time']
        for attribute in summary_attributes:
            # Calculate a weighted average of problems and questions
            problem_average = context['problems_total'][attribute]
            question_average = context['questions_total'][attribute]
            problem_count = context['problems_total'][attribute+"_count"]
            question_count = context['questions_total'][attribute+"_count"]
            if problem_count != 0 and question_count != 0:
                numerator = ((problem_average*problem_count) + (question_average*question_count))
                denominator = (problem_count + question_count)
                issues_total[attribute] = numerator / denominator
            elif problem_count != 0:
                issues_total[attribute] = problem_average
            else:
                issues_total[attribute] = question_average
        context['issues_total'] = issues_total

        return context

class OrganisationProblems(MessageListMixin,
                           TemplateView):
    template_name = 'organisations/organisation-problems.html'
    message_type = 'problem'

    def get_issues(self, organisation):
        return organisation.problem_set.all()

class OrganisationQuestions(MessageListMixin,
                            TemplateView):
    template_name = 'organisations/organisation-questions.html'
    message_type = 'question'

    def get_issues(self, organisation):
        return organisation.question_set.all()

class OrganisationReviews(OrganisationAwareViewMixin,
                          TemplateView):
    template_name = 'organisations/organisation-reviews.html'

    def get_context_data(self, **kwargs):
        context = super(OrganisationReviews, self).get_context_data(**kwargs)
        if 'private' in kwargs and kwargs['private'] == True:
            context['private'] = True
        else:
            context['private'] = False
        return context

class Summary(TemplateView):
    template_name = 'organisations/summary.html'

    def get_context_data(self, **kwargs):
        issue_types = {'problems': Problem,
                       'questions': Question}

        context = super(Summary, self).get_context_data(**kwargs)

        # Set up the data for the filters
        context['problems_categories'] = Problem.CATEGORY_CHOICES
        context['problems_statuses'] = Problem.STATUS_CHOICES
        context['questions_categories'] = Question.CATEGORY_CHOICES
        context['questions_statuses'] = Question.STATUS_CHOICES
        context['organisation_types'] = settings.ORGANISATION_CHOICES
        context['issue_types'] = [(value, model_type.__name__) for value, model_type  in issue_types.items()]
        context['services'] = Service.service_codes()
        filters = {}
        issue_type = self.request.GET.get('issue_type')

        # Default to showing problems
        if not issue_type in issue_types.keys():
            issue_type = 'problems'
        context['issue_type'] = issue_type
        model_class = issue_types[issue_type]

        # Service code filter
        selected_service = self.request.GET.get('service')
        if selected_service in dict(context['services']):
            filters['service_code'] = selected_service

        # Category filter
        category = self.request.GET.get('%s_category' % issue_type)
        if category in dict(model_class.CATEGORY_CHOICES):
            filters['%s_category' % issue_type] = category
            filters['category'] = category

        # Organisation type
        organisation_type = self.request.GET.get('organisation_type')
        if organisation_type in settings.ORGANISATION_TYPES:
            filters['organisation_type'] = organisation_type

        # Status
        status = self.request.GET.get('%s_status' % issue_type)
        if status and status != 'all' and int(status) in dict(model_class.STATUS_CHOICES):
            filters['%s_status' % issue_type] = int(status)
            filters['status'] = int(status)

        organisation_rows = interval_counts(issue_type=model_class, filters=filters)
        organisations_table = NationalSummaryTable(organisation_rows, cobrand=kwargs['cobrand'])
        RequestConfig(self.request).configure(organisations_table)
        context['organisations_table'] = organisations_table
        context['filters'] = filters
        return context

class OrganisationDashboard(OrganisationAwareViewMixin,
                            OrganisationIssuesAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'
