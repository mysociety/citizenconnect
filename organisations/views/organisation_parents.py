# Django imports
from django.views.generic import TemplateView
from django.http import Http404

from django_tables2 import RequestConfig

# App imports
from issues.models import Problem

from ..auth import enforce_organisation_parent_access_check
from ..models import OrganisationParent
from ..lib import interval_counts
from ..tables import ProblemDashboardTable

from .base import PrivateViewMixin, FilterFormMixin


class OrganisationParentAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    Organisation Parent, such as organisation parent dashboards."""

    def dispatch(self, request, *args, **kwargs):
        # Set organisation_parent here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        try:
            self.organisation_parent = OrganisationParent.objects.get(code=kwargs['code'])
        except OrganisationParent.DoesNotExist:
            raise Http404
        return super(OrganisationParentAwareViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationParentAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation_parent'] = self.organisation_parent
        # Check that the user can access the organisation_parent if this is private
        if context['private']:
            enforce_organisation_parent_access_check(context['organisation_parent'], self.request.user)
        return context


class OrganisationParentSummary(OrganisationParentAwareViewMixin, FilterFormMixin, TemplateView):
    template_name = 'organisations/organisation_parent_summary.html'

    def get_form_kwargs(self):
        kwargs = super(OrganisationParentSummary, self).get_form_kwargs()
        kwargs['with_ccg'] = False
        kwargs['with_organisation_type'] = False
        kwargs['with_service_code'] = False
        kwargs['with_status'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganisationParentSummary, self).get_context_data(**kwargs)

        organisation_parent = context['organisation_parent']
        organisation_ids = [org.id for org in organisation_parent.organisations.all()]

        # Check that the trust has some organisations attached to it
        if len(organisation_ids) > 0:
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


class OrganisationParentDashboard(OrganisationParentAwareViewMixin,
                                  TemplateView):
    template_name = 'organisations/organisation_parent_dashboard.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(OrganisationParentDashboard, self).get_context_data(**kwargs)

        # Get the models related to this organisation, and let the db sort them
        problems = context['organisation_parent'].problem_set.open_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
        return context
