# Django imports
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied

from ..auth import user_is_superuser
from ..models import SuperuserLogEntry, CCG, OrganisationParent


class SuperuserOnlyMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not user_is_superuser(request.user):
            raise PermissionDenied()
        return super(SuperuserOnlyMixin, self).dispatch(request, *args, **kwargs)


class SuperuserDashboard(SuperuserOnlyMixin, TemplateView):
    template_name = 'organisations/superuser_dashboard.html'

    def get_context_data(self, **kwargs):

        context = super(SuperuserDashboard, self).get_context_data(**kwargs)
        context['ccgs'] = CCG.objects.all()
        context['organisation_parents'] = OrganisationParent.objects.all()

        return context


class SuperuserLogs(SuperuserOnlyMixin, TemplateView):

    template_name = 'organisations/superuser_logs.html'

    def get_context_data(self, **kwargs):
        context = super(SuperuserLogs, self).get_context_data(**kwargs)
        context['logs'] = SuperuserLogEntry.objects.all()
        return context
