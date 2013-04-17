# Standard imports
from itertools import chain
from operator import attrgetter
import json

# Django imports
from django.views.generic import FormView, TemplateView, UpdateView, ListView
from django.views.generic.edit import FormMixin
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
from .auth import user_in_group, user_in_groups, user_is_superuser, check_organisation_access, check_question_access, user_can_access_escalation_dashboard
from .models import Organisation, Service, CCG, SuperuserLogEntry
from .forms import OrganisationFinderForm, FilterForm
from .lib import interval_counts
from .tables import NationalSummaryTable, ProblemTable, ExtendedProblemTable, QuestionsDashboardTable, ProblemDashboardTable, EscalationDashboardTable, BreachTable

class PrivateViewMixin(object):
    """
    Mixin for views which need access to a context variable indicating whether the view
    is being accessed in a private context, only accessible to logged-in users.
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


class FilterFormMixin(FormMixin):
    """
    Mixin for views which have a filter form
    """
    form_class = FilterForm

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        form.is_valid()
        kwargs['form'] = form
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_form_kwargs(self):
        # Pass form kwargs from GET instead of POST
        kwargs = {'initial': self.get_initial()}
        if self.request.GET:
            kwargs['data'] = self.request.GET
        if 'private' in self.kwargs and self.kwargs['private'] == True:
            kwargs['private'] = True
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FilterFormMixin, self).get_context_data(**kwargs)
        form = context['form']
        selected_filters = {}
        if hasattr(form, 'cleaned_data'):
            for name, value in form.cleaned_data.items():
                if value:
                    selected_filters[name] = value
        context['selected_filters'] = selected_filters
        return context

class Map(PrivateViewMixin, TemplateView):
    template_name = 'organisations/map.html'

    def get_context_data(self, **kwargs):
        context = super(Map, self).get_context_data(**kwargs)

        # TODO - Filter by location
        organisations = Organisation.objects.all().order_by("id")

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
    issue_type = 'problem'

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
                return render(self.request, self.form_template_name, {'form': form,
                                                                      'issue_type': self.issue_type})
        else:
              return render(self.request, self.form_template_name, {'form': OrganisationFinderForm(),
                                                                    'issue_type': self.issue_type})

class OrganisationSummary(OrganisationAwareViewMixin,
                          TemplateView):
    template_name = 'organisations/organisation_summary.html'

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

        if context['private']:
            status_rows = Problem.STATUS_CHOICES
            volume_statuses = Problem.ALL_STATUSES
        else:
            status_rows = Problem.VISIBLE_STATUS_CHOICES
            volume_statuses = Problem.VISIBLE_STATUSES
        summary_stats_statuses = Problem.VISIBLE_STATUSES
        count_filters['status'] = tuple(volume_statuses)
        context['problems_total'] = interval_counts(issue_type=Problem,
                                                    filters=count_filters,
                                                    organisation_id=organisation.id)
        count_filters['status'] = tuple(summary_stats_statuses)
        context['problems_summary_stats'] = interval_counts(issue_type=Problem,
                                                            filters=count_filters,
                                                            organisation_id=organisation.id)
        status_list = []
        for status, description in status_rows:
            count_filters['status'] = (status,)
            status_counts = interval_counts(issue_type=Problem,
                                            filters=count_filters,
                                            organisation_id=organisation.id)
            del count_filters['status']
            status_counts['description'] = description
            status_counts['status'] = status
            if status in Problem.VISIBLE_STATUSES:
                status_counts['hidden'] = False
            else:
                status_counts['hidden'] = True
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
            issues_total[attribute] = context['problems_summary_stats'][attribute]
        context['issues_total'] = issues_total

        return context

class OrganisationProblems(OrganisationAwareViewMixin,
                           TemplateView):
    template_name = 'organisations/organisation_problems.html'

    def get_issues(self, organisation, private):
        if private:
            return organisation.problem_set.all()
        else:
            return organisation.problem_set.all_moderated_published_problems()

    def get_context_data(self, **kwargs):
        context = super(OrganisationProblems, self).get_context_data(**kwargs)

        table_args = {'private': context['private']}
        if not context['private']:
            table_args['cobrand'] = kwargs['cobrand']

        issues = self.get_issues(context['organisation'], context['private'])
        if context['organisation'].has_services() and context['organisation'].has_time_limits():
            issue_table = ExtendedProblemTable(issues, **table_args)
        else:
            issue_table = ProblemTable(issues, **table_args)

        RequestConfig(self.request, paginate={'per_page': 8}).configure(issue_table)
        context['table'] = issue_table
        context['page_obj'] = issue_table.page
        return context

class OrganisationReviews(OrganisationAwareViewMixin,
                          TemplateView):
    template_name = 'organisations/organisation_reviews.html'

class Summary(FilterFormMixin, PrivateViewMixin, TemplateView):
    template_name = 'organisations/summary.html'

    def get_context_data(self, **kwargs):
        context = super(Summary, self).get_context_data(**kwargs)

        # Build a dictionary of filters in the format we can pass
        # into interval_counts to filter the problems we make a
        # summary for
        interval_filters = context['selected_filters']

        if interval_filters.get('status'):
            # ignore a filter request for a hidden status
            if not interval_filters['status'] in Problem.VISIBLE_STATUSES:
                del interval_filters['status']

        if not interval_filters.get('status'):
            # by default the status should filter for visible statuses
            interval_filters['status'] = tuple(Problem.VISIBLE_STATUSES)

        threshold = None
        if settings.SUMMARY_THRESHOLD:
            threshold = settings.SUMMARY_THRESHOLD
        organisation_rows = interval_counts(issue_type=Problem,
                                            filters=interval_filters,
                                            threshold=threshold)
        organisations_table = NationalSummaryTable(organisation_rows, cobrand=kwargs['cobrand'])
        RequestConfig(self.request, paginate={"per_page": 8}).configure(organisations_table)
        context['table'] = organisations_table
        context['page_obj'] = organisations_table.page
        return context

class OrganisationDashboard(OrganisationAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(OrganisationDashboard, self).get_context_data(**kwargs)

        # Get the models related to this organisation, and let the db sort them
        problems = context['organisation'].problem_set.open_unescalated_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
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

    # CQC, CCG, and customer contact centre users go to the escalation dashboard
    elif user_in_groups(user, [auth.CQC, auth.CCG, auth.CUSTOMER_CONTACT_CENTRE]):
        return HttpResponseRedirect(reverse('escalation-dashboard'))

    # Moderators go to the moderation queue
    elif user_in_group(user, auth.CASE_HANDLERS):
        return HttpResponseRedirect(reverse('moderate-home'))

    elif user_in_group(user, auth.SECOND_TIER_MODERATORS):
        return HttpResponseRedirect(reverse('second-tier-moderate-home'))

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

    queryset = Question.objects.open_questions()
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

class EscalationDashboard(FilterFormMixin, TemplateView):

    template_name = 'organisations/escalation_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not user_can_access_escalation_dashboard(request.user):
            raise PermissionDenied()
        return super(EscalationDashboard, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EscalationDashboard, self).get_form_kwargs()

        # Turn off the ccg filter if the user is a ccg
        user = self.request.user
        if not user_is_superuser(user) and not user_in_groups(user, [auth.CQC, auth.CUSTOMER_CONTACT_CENTRE]):
            kwargs['with_ccg'] = False

        # Turn off status too, because all problems on this dashboard have
        # a status of Escalated
        kwargs['with_status'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EscalationDashboard, self).get_context_data(**kwargs)

        problems = Problem.objects.open_escalated_problems()
        user = self.request.user

        # Restrict problem queryset for non-CQC and non-superuser users (i.e. CCG users)
        if not user_is_superuser(user) and not user_in_groups(user, [auth.CQC, auth.CUSTOMER_CONTACT_CENTRE]):
            problems = problems.filter(organisation__escalation_ccg__in=(user.ccgs.all()),
                                       commissioned=Problem.LOCALLY_COMMISSIONED)
        # Restrict problem queryset for non CQC and non-CCG users (i.e. Customer Contact Centre)
        elif not user_is_superuser(user) and not user_in_groups(user, [auth.CQC, auth.CCG]):
            problems = problems.filter(commissioned=Problem.NATIONALLY_COMMISSIONED)

        # Apply form filters on top of this
        filtered_problems = self.apply_filters(context['selected_filters'], problems)

        # Setup a table for the problems
        problem_table = EscalationDashboardTable(filtered_problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context

    def apply_filters(self, filters, queryset):
        filtered_queryset = queryset
        for name, value in filters.items():
            if name == 'category':
                filtered_queryset = filtered_queryset.filter(category=value)
            if name == 'organisation_type':
                filtered_queryset = filtered_queryset.filter(organisation__organisation_type=value)
            if name == 'service_code':
                filtered_queryset = filtered_queryset.filter(service__service_code=value)
            if name == 'ccg':
                # ccg is a CCG model instance
                filtered_queryset = filtered_queryset.filter(organisation__ccgs__id__exact=value.id)
            if name == 'breach':
                filtered_queryset = filtered_queryset.filter(breach=value)
        return filtered_queryset

class EscalationBreaches(TemplateView):

    template_name = 'organisations/escalation_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        if not user_can_access_escalation_dashboard(request.user):
            raise PermissionDenied()
        return super(EscalationBreaches, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EscalationBreaches, self).get_context_data(**kwargs)
        problems = Problem.objects.open_problems().filter(breach=True)

        # Restrict problem queryset for non-CQC and non-superuser users (i.e. CCG users)
        user = self.request.user
        if not user_is_superuser(user) and not user_in_groups(user, [auth.CQC, auth.CUSTOMER_CONTACT_CENTRE]):
            problems = problems.filter(organisation__escalation_ccg__in=(user.ccgs.all()))
        # Everyone else see's all breaches

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context
