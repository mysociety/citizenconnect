# Django imports
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django_tables2 import RequestConfig

# App imports
from issues.models import Problem

from .. import auth
from ..auth import (user_in_group,
                    user_can_access_national_escalation_dashboard)
from ..models import Organisation
from ..tables import (ProblemDashboardTable,
                      BreachTable)

from .base import FilterFormMixin


class EscalationDashboard(FilterFormMixin, TemplateView):

    template_name = 'organisations/escalation_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        self.enforce_access(request.user)
        return super(EscalationDashboard, self).dispatch(request, *args, **kwargs)

    def enforce_access(self, user):
        if not user_can_access_national_escalation_dashboard(user):
            raise PermissionDenied()

    def get_form_kwargs(self):
        kwargs = super(EscalationDashboard, self).get_form_kwargs()
        kwargs['organisations'] = self.get_organisations()
        # Turn off status because all problems on this dashboard have
        # a status of Escalated
        kwargs['with_status'] = False

        return kwargs

    def get_organisations(self):
        return Organisation.objects.all()

    def get_problems(self):
        problems = Problem.objects.open_escalated_problems()
        user = self.request.user

        # Restrict problem queryset for Customer Contact Centre users
        if user_in_group(user, auth.CUSTOMER_CONTACT_CENTRE):
            problems = problems.filter(commissioned=Problem.NATIONALLY_COMMISSIONED)

        return problems

    def get_context_data(self, **kwargs):
        context = super(EscalationDashboard, self).get_context_data(**kwargs)

        problems = self.get_problems()

        # Apply form filters on top of this
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Setup a table for the problems
        problem_table = ProblemDashboardTable(filtered_problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        context['tabs_template'] = 'organisations/includes/escalation_tabs.html'

        return context


class EscalationBreaches(TemplateView):

    template_name = 'organisations/escalation_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        self.enforce_access(request.user)
        return super(EscalationBreaches, self).dispatch(request, *args, **kwargs)

    def enforce_access(self, user):
        if not user_can_access_national_escalation_dashboard(user):
            raise PermissionDenied()

    def get_problems(self):
        return Problem.objects.open_problems().filter(breach=True)

    def get_context_data(self, **kwargs):
        context = super(EscalationBreaches, self).get_context_data(**kwargs)

        problems = self.get_problems()

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        context['tabs_template'] = 'organisations/includes/escalation_tabs.html'

        return context
