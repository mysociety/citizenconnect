# Django imports
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

# App imports
from issues.models import Problem

from ..auth import enforce_trust_access_check
from ..models import Organisation, OrganisationParent
from ..lib import interval_counts
from ..tables import (TrustProblemTable,
                      ProblemDashboardTable,
                      BreachTable)

from .base import PrivateViewMixin, FilterFormMixin


class OrganisationParentAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    trust, such as trust dashboards."""

    def dispatch(self, request, *args, **kwargs):
        # Set trust here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.trust = OrganisationParent.objects.get(code=kwargs['code'])
        return super(OrganisationParentAwareViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationParentAwareViewMixin, self).get_context_data(**kwargs)
        context['trust'] = self.trust
        # Check that the user can access the trust if this is private
        if context['private']:
            enforce_trust_access_check(context['trust'], self.request.user)
        return context


class TrustSummary(OrganisationParentAwareViewMixin, FilterFormMixin, TemplateView):
    template_name = 'organisations/trust_summary.html'

    def get_form_kwargs(self):
        kwargs = super(TrustSummary, self).get_form_kwargs()
        kwargs['with_ccg'] = False
        kwargs['with_organisation_type'] = False
        kwargs['with_service_code'] = False
        kwargs['with_status'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(TrustSummary, self).get_context_data(**kwargs)

        trust = context['trust']
        organisation_ids = [org.id for org in trust.organisations.all()]

        # Load the user-selected filters from the form
        count_filters = context['selected_filters']

        status_rows = Problem.STATUS_CHOICES
        volume_statuses = Problem.ALL_STATUSES

        summary_stats_statuses = Problem.VISIBLE_STATUSES
        count_filters['status'] = tuple(volume_statuses)
        organisation_filters = {'organisation_ids': tuple(organisation_ids)}
        context['problems_total'] = self.get_interval_counts(problem_filters=count_filters,
                                                             organisation_filters=organisation_filters)
        count_filters['status'] = tuple(summary_stats_statuses)
        count_filters = self.translate_flag_filters(count_filters)

        context['problems_summary_stats'] = self.get_interval_counts(problem_filters=count_filters,
                                                                     organisation_filters=organisation_filters)
        status_list = []
        for status, description in status_rows:
            count_filters['status'] = (status,)
            status_counts = self.get_interval_counts(problem_filters=count_filters,
                                                     organisation_filters=organisation_filters)
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

    def get_interval_counts(self, problem_filters, organisation_filters):
        organisation_problem_data = interval_counts(problem_filters=problem_filters,
                                                    organisation_filters=organisation_filters)

        count_attributes = ['all_time',
                            'week',
                            'four_weeks',
                            'six_months']

        average_attributes = ['happy_service',
                              'happy_outcome',
                              'average_time_to_acknowledge',
                              'average_time_to_address']

        summary_attributes = count_attributes + average_attributes

        organisation_data = {}

        for attribute in summary_attributes:
            organisation_data[attribute] = 0

        # Aggregate data
        for org_data in organisation_problem_data:
            for attribute in summary_attributes:
                if attribute in org_data and not org_data[attribute] is None:
                    organisation_data[attribute] += org_data[attribute]

        for attribute in average_attributes:
            organisation_data[attribute] = organisation_data[attribute] / len(organisation_problem_data)

        return organisation_data


class TrustProblems(OrganisationParentAwareViewMixin,
                    FilterFormMixin,
                    TemplateView):

    template_name = 'organisations/trust_problems.html'

    def get_form_kwargs(self):
        kwargs = super(TrustProblems, self).get_form_kwargs()

        # Turn off the ccg filter and filter organisations to this trust
        kwargs['with_ccg'] = False
        kwargs['organisations'] = Organisation.objects.filter(parent=self.trust)

        # Turn off the organisation_type filter
        kwargs['with_organisation_type'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(TrustProblems, self).get_context_data(**kwargs)

        # Get a queryset of issues and apply any filters to them
        problems = self.trust.problem_set.all()
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Build a table
        table_args = {'private': context['private']}
        problem_table = TrustProblemTable(filtered_problems, **table_args)

        RequestConfig(self.request, paginate={'per_page': 8}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context


class TrustDashboard(OrganisationParentAwareViewMixin,
                     TemplateView):
    template_name = 'organisations/trust_dashboard.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(TrustDashboard, self).get_context_data(**kwargs)

        # Get the models related to this organisation, and let the db sort them
        problems = context['trust'].problem_set.open_unescalated_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
        return context


class TrustBreaches(OrganisationParentAwareViewMixin,
                    TemplateView):

    template_name = 'organisations/trust_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        return super(TrustBreaches, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrustBreaches, self).get_context_data(**kwargs)
        problems = Problem.objects.open_problems().filter(breach=True, organisation__parent=context['trust'])

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        return context
