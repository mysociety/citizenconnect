
class SuperuserDashboard(TemplateView):
    template_name = 'organisations/superuser_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        self.enforce_access(request.user)
        return super(SuperuserDashboard, self).dispatch(request, *args, **kwargs)

    def enforce_access(self, user):
        if not user_can_access_superuser_dashboard(user):
            raise PermissionDenied()

    def get_context_data(self, **kwargs):

        context = super(SuperuserDashboard, self).get_context_data(**kwargs)
        context['ccgs'] = CCG.objects.all()
        context['organisation_parents'] = OrganisationParent.objects.all()

        return context


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
