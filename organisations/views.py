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
from issues.models import Problem

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
    organisation, such as problem forms."""

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation'] = Organisation.objects.get(ods_code=self.kwargs['ods_code'])
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
            issue_table = ExtendedMessageModelTable(self.get_issues(organisation, context['private']), **table_args)
        else:
            issue_table = MessageModelTable(self.get_issues(organisation, context['private']), **table_args)
        context['organisation'] = organisation
        RequestConfig(self.request, paginate={'per_page': 8}).configure(issue_table)
        context['table'] = issue_table
        context['page_obj'] = issue_table.page
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

            # Counts on private map are all open problems, regardless of moderation
            if context['private']:
                organisation_dict['problem_count'] = organisation.problem_set.open_problems().count()
            # Counts on public map don't include un-moderated or hidden issues, but do include private issues
            else:
                organisation_dict['problem_count'] = organisation.problem_set.open_moderated_published_problems().count()

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
        if context.has_key('selected_service'):
            count_filters['service_id'] = selected_service
        category = self.request.GET.get('problems_category')
        if category in dict(Problem.CATEGORY_CHOICES):
            context['problems_category'] = category
            count_filters['category'] = category
        context['problems_categories'] = Problem.CATEGORY_CHOICES

        context['problems_total'] = interval_counts(issue_type=Problem,
                                                    filters=count_filters,
                                                    organisation_id=organisation.id)

        status_list = []
        for status, description in Problem.STATUS_CHOICES:
            count_filters['status'] = status
            status_counts = interval_counts(issue_type=Problem,
                                            filters=count_filters,
                                            organisation_id=organisation.id)
            del count_filters['status']
            status_counts['description'] = description
            status_list.append(status_counts)
        context['problems_by_status'] = status_list

        # Generate a dictionary of overall issue boolean counts to use in the summary
        # statistics
        issues_total = {}
        summary_attributes = ['happy_service',
                              'happy_outcome',
                              'average_time_to_acknowledge',
                              'average_time_to_address']
        for attribute in summary_attributes:
            problem_average = context['problems_total'][attribute]
            issues_total[attribute] = problem_average
        context['issues_total'] = issues_total

        return context

class OrganisationProblems(MessageListMixin,
                           TemplateView):
    template_name = 'organisations/organisation-problems.html'
    message_type = 'problem'

    def get_issues(self, organisation, private):
        if private:
            return organisation.problem_set.all()
        else:
            return organisation.problem_set.all_moderated_published_public_problems()

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

        context = super(Summary, self).get_context_data(**kwargs)

        # Set up the data for the filters
        context['problem_categories'] = Problem.CATEGORY_CHOICES
        context['problem_statuses'] = Problem.STATUS_CHOICES
        context['organisation_types'] = settings.ORGANISATION_CHOICES
        context['services'] = Service.service_codes()
        filters = {}

        # Service code filter
        selected_service = self.request.GET.get('service')
        if selected_service in dict(context['services']):
            filters['service_code'] = selected_service

        # Category filter
        category = self.request.GET.get('problem_category')
        if category in dict(Problem.CATEGORY_CHOICES):
            filters['problem_category'] = category
            filters['category'] = category

        # Organisation type filter
        organisation_type = self.request.GET.get('organisation_type')
        if organisation_type in settings.ORGANISATION_TYPES:
            filters['organisation_type'] = organisation_type

        # Status filter
        status = self.request.GET.get('problem_status')
        if status and status != 'all' and int(status) in dict(Problem.STATUS_CHOICES):
            filters['problem_status'] = int(status)
            filters['status'] = int(status)

        organisation_rows = interval_counts(issue_type=Problem, filters=filters)
        organisations_table = NationalSummaryTable(organisation_rows, cobrand=kwargs['cobrand'])
        RequestConfig(self.request, paginate={"per_page": 8}).configure(organisations_table)
        context['table'] = organisations_table
        context['page_obj'] = organisations_table.page
        context['filters'] = filters
        return context

class OrganisationDashboard(OrganisationAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(OrganisationDashboard, self).get_context_data(**kwargs)
        # Get the models related to this organisation, and let the db sort them
        problems = context['organisation'].problem_set.open_problems()
        context['problems'] = problems
        return context
