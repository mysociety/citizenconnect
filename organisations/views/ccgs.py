# Django imports
from django.views.generic import TemplateView
from django.http import Http404

from django_tables2 import RequestConfig

from ..auth import enforce_ccg_access_check
from ..models import CCG, Problem
from ..tables import ProblemDashboardTable, CCGSummaryTable

from .base import PrivateViewMixin, EscalationDashboard, EscalationBreaches, Summary


class CCGAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    ccg, such as ccg dashboards"""

    def dispatch(self, request, *args, **kwargs):
        # Lookup and set ccg here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        try:
            self.ccg = CCG.objects.get(code=kwargs['code'])
        except CCG.DoesNotExist:
            raise Http404
        return super(CCGAwareViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CCGAwareViewMixin, self).get_context_data(**kwargs)
        context['ccg'] = self.ccg
        # Check that the user can access the ccg if this is private
        if context['private']:
            enforce_ccg_access_check(context['ccg'], self.request.user)
        return context


class CCGDashboard(CCGAwareViewMixin, TemplateView):
    template_name = 'organisations/ccg_dashboard.html'

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CCGDashboard, self).get_context_data(**kwargs)

        # Get the problems related to this ccg, and let the db sort them
        problems = context['ccg'].problem_set.open_unescalated_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
        return context


class CCGEscalationDashboard(CCGAwareViewMixin, EscalationDashboard):

    template_name = 'organisations/escalation_dashboard.html'

    def enforce_access(self, user):
        enforce_ccg_access_check(self.ccg, user)

    def get_form_kwargs(self):
        kwargs = super(CCGEscalationDashboard, self).get_form_kwargs()
        kwargs['with_ccg'] = False
        return kwargs

    def get_organisations(self):
        organisations = super(CCGEscalationDashboard, self).get_organisations()
        return organisations.filter(parent__escalation_ccg=self.ccg)

    def get_problems(self):
        problems = super(CCGEscalationDashboard, self).get_problems()
        # Filter to the current CCG
        return problems.filter(organisation__parent__escalation_ccg=self.ccg,
                               commissioned=Problem.LOCALLY_COMMISSIONED)

    def get_context_data(self, **kwargs):
        context = super(CCGEscalationDashboard, self).get_context_data(**kwargs)
        context['tabs_template'] = 'organisations/includes/ccg_tabs.html'

        return context


class CCGEscalationBreaches(CCGAwareViewMixin, EscalationBreaches):

    template_name = 'organisations/escalation_breaches.html'

    def enforce_access(self, user):
        enforce_ccg_access_check(self.ccg, user)

    def get_problems(self):
        problems = super(CCGEscalationBreaches, self).get_problems()
        # Filter them to the current ccg
        problems = problems.filter(organisation__parent__escalation_ccg=self.ccg)
        return problems

    def get_context_data(self, **kwargs):
        context = super(CCGEscalationBreaches, self).get_context_data(**kwargs)
        context['tabs_template'] = 'organisations/includes/ccg_tabs.html'

        return context


class CCGSummary(CCGAwareViewMixin, Summary):
    template_name = 'organisations/ccg_summary.html'
    permitted_statuses = Problem.ALL_STATUSES
    summary_table_class = CCGSummaryTable

    def dispatch(self, request, *args, **kwargs):
        enforce_ccg_access_check(self.ccg, request.user)
        return super(CCGSummary, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(CCGSummary, self).get_form_kwargs()
        kwargs['with_ccg'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        # default the cobrand
        if 'cobrand' not in kwargs:
            kwargs['cobrand'] = None
        return super(CCGSummary, self).get_context_data(**kwargs)

    def get_interval_counts(self, problem_filters, organisation_filters, threshold):
        # Filter to the selected CCG
        organisation_filters['ccg'] = tuple([self.ccg.id])
        return super(CCGSummary, self).get_interval_counts(problem_filters=problem_filters,
                                                           organisation_filters=organisation_filters,
                                                           threshold=threshold)
