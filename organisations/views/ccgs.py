# Django imports
from django.views.generic import TemplateView
from django_tables2 import RequestConfig

from ..auth import enforce_ccg_access_check
from ..models import CCG
from ..tables import ProblemDashboardTable

from .base import PrivateViewMixin


class CCGAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    ccg, such as ccg dashboards"""

    def dispatch(self, request, *args, **kwargs):
        # If there is a code in the kwargs, we assume we want a ccg.
        # So we lookup and set ccg here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.ccg = CCG.objects.get(code=kwargs['code'])
        return super(CCGAwareViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CCGAwareViewMixin, self).get_context_data(**kwargs)
        context['ccg'] = self.ccg
        # Check that the user can access the ccg if this is private
        if context['private']:
            enforce_ccg_access_check(context['ccg'], self.request.user)
        return context


class CCGDashboard(PrivateViewMixin, TemplateView):
    template_name = 'organisations/ccg_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        # Set ccg here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.ccg = CCG.objects.get(code=kwargs['code'])
        return super(CCGDashboard, self).dispatch(request, *args, **kwargs)

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(CCGDashboard, self).get_context_data(**kwargs)
        context['ccg'] = self.ccg
        # Check that the user can access the ccg if this is private
        if context['private']:
            enforce_ccg_access_check(context['ccg'], self.request.user)

        # Get the problems related to this ccg, and let the db sort them
        problems = context['ccg'].problem_set.open_unescalated_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
        return context