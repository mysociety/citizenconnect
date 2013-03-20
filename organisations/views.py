# Standard imports
from itertools import chain
from operator import attrgetter
import json

# Django imports
from django.views.generic import FormView, TemplateView, UpdateView, ListView
from django.template.defaultfilters import escape
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django_tables2 import RequestConfig
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q

# App imports
from citizenconnect.shortcuts import render
from issues.models import Problem, Question

import choices_api
import auth
from .auth import user_in_group, user_in_groups, user_is_superuser, check_organisation_access, check_question_access
from .models import Organisation, Service, CCG, SuperuserLogEntry
from .forms import OrganisationFinderForm
from .lib import interval_counts
from .tables import NationalSummaryTable, MessageModelTable, ExtendedMessageModelTable, QuestionsDashboardTable

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

class OrganisationAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    organisation, such as problem forms."""

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation'] = Organisation.objects.get(ods_code=self.kwargs['ods_code'])
        # Check that the user can access the organisation if this is private
        if context['private']:
            check_organisation_access(context['organisation'], self.request.user)
        return context

class MessageListMixin(OrganisationAwareViewMixin):
    """Mixin class for views which need to display a list of issues belonging to an organisation
       in either a public or private context"""

    def get_context_data(self, **kwargs):
        context = super(MessageListMixin, self).get_context_data(**kwargs)

        table_args = {'private': context['private'],
                      'message_type': self.message_type}
        if not context['private']:
            table_args['cobrand'] = kwargs['cobrand']

        issues = self.get_issues(context['organisation'], context['private'])
        if context['organisation'].has_services() and context['organisation'].has_time_limits():
            issue_table = ExtendedMessageModelTable(issues, **table_args)
        else:
            issue_table = MessageModelTable(issues, **table_args)

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

        # Check that the user is a superuser
        if context['private']:
            if not user_is_superuser(self.request.user):
                raise PermissionDenied()

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
    template_name = 'provider_results.html'
    form_template_name = 'pick_provider.html'
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
    template_name = 'organisations/organisation_problems.html'
    message_type = 'problem'

    def get_issues(self, organisation, private):
        if private:
            return organisation.problem_set.all()
        else:
            return organisation.problem_set.all_moderated_published_problems()

class OrganisationReviews(OrganisationAwareViewMixin,
                          TemplateView):
    template_name = 'organisations/organisation_reviews.html'

class Summary(TemplateView):
    template_name = 'organisations/summary.html'

    def get_context_data(self, **kwargs):

        context = super(Summary, self).get_context_data(**kwargs)

        # Set up the data for the filters
        context['problem_categories'] = Problem.CATEGORY_CHOICES
        context['problem_statuses'] = Problem.STATUS_CHOICES
        context['organisation_types'] = settings.ORGANISATION_CHOICES
        context['services'] = Service.service_codes()
        context['ccgs'] = CCG.objects.all()
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
        context['problems_total'] = interval_counts(issue_type=Problem,
                                                    filters={},
                                                    organisation_id=context['organisation'].id)
        return context

class DashboardChoice(TemplateView):

    template_name = 'organisations/dashboard_choice.html'

    def get_context_data(self, **kwargs):
        context = super(DashboardChoice, self).get_context_data(**kwargs)
        # Get all the organisations the user can see
        context['organisations'] = self.request.user.organisations.all()
        return context

@login_required
def login_redirect(request):
    """
    View function to redirect a logged in user to the right url after logging in.
    Allows users to have an effective "homepage" which they go to automatically
    after logging in. Uses their user group to determine what is the right page.
    """

    user = request.user

    # NHS Super users get a special map page
    if user_in_group(user, auth.NHS_SUPERUSERS):
        return HttpResponseRedirect(reverse('private-map'))

    # Moderators go to the moderation queue
    elif user_in_group(user, auth.CASE_HANDLERS):
        return HttpResponseRedirect(reverse('moderate-home'))

    # Question Answerers go to the question answering dashboard
    elif user_in_group(user, auth.QUESTION_ANSWERERS):
        return HttpResponseRedirect(reverse('questions-dashboard'))

    # Providers
    elif user_in_group(user, auth.PROVIDERS):
        # Providers with only one organisation just go to that organisation's dashboard
        if user.organisations.count() == 1:
            organisation = user.organisations.all()[0]
            return HttpResponseRedirect(reverse('org-dashboard', kwargs={'ods_code':organisation.ods_code}))
        # Providers with more than one provider attached
        # go to a page to choose which one to see
        elif user.organisations.count() > 1:
            return HttpResponseRedirect(reverse('dashboard-choice'))

    # Anyone else goes to the normal homepage
    return HttpResponseRedirect(reverse('home', kwargs={'cobrand':'choices'}))

class SuperuserLogs(TemplateView):

    template_name = 'organisations/superuser_logs.html'

    def get_context_data(self, **kwargs):
        context = super(SuperuserLogs, self).get_context_data(**kwargs)
        # Only NHS superusers can see this page
        if not user_is_superuser(self.request.user):
            raise PermissionDenied()
        else:
            context['logs'] = SuperuserLogEntry.objects.all()
        return context

class QuestionsDashboard(ListView):

    queryset = Question.objects.open_questions();
    template_name = 'organisations/questions_dashboard.html'
    context_object_name = "questions"

    def dispatch(self, request, *args, **kwargs):
        check_question_access(request.user)
        return super(QuestionsDashboard, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuestionsDashboard, self).get_context_data(**kwargs)
        # Setup a table for the questions
        question_table = QuestionsDashboardTable(context['questions'])
        RequestConfig(self.request, paginate={'per_page': 25}).configure(question_table)
        context['table'] = question_table
        context['page_obj'] = context['table'].page
        return context
