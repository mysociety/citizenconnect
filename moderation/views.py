from itertools import chain
from operator import attrgetter

# Django imports
from django.views.generic import TemplateView, UpdateView
from django.views.generic.edit import FormView
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect

from django_tables2 import RequestConfig

# App imports
from issues.models import Problem
from organisations.models import Organisation
import organisations.auth as auth
from organisations.auth import user_in_group

from .forms import LookupForm, ProblemModerationForm
from .tables import ModerationTable

class ModeratorsOnlyMixin(object):
    """
    Mixin to protect views using the user_passes_test decorator
    """

    def dispatch(self, request, *args, **kwargs):
        if not user_in_group(request.user, auth.CASE_HANDLERS):
            raise PermissionDenied()
        else:
            return super(ModeratorsOnlyMixin, self).dispatch(request, *args, **kwargs)

class ModerateHome(ModeratorsOnlyMixin,
                   TemplateView):
    template_name = 'moderation/moderate-home.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(ModerateHome, self).get_context_data(**kwargs)
        context['issues'] = Problem.objects.unmoderated_problems().order_by("-created")
        # Setup a table for the problems
        issue_table = ModerationTable(context['issues'])
        RequestConfig(self.request, paginate={'per_page': 25}).configure(issue_table)
        context['table'] = issue_table
        context['page_obj'] = context['table'].page
        return context

class ModerateLookup(ModeratorsOnlyMixin,
                     FormView):
    template_name = 'moderation/moderate-lookup.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        context = RequestContext(self.request)
        moderate_url = reverse("moderate-form", kwargs={'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(moderate_url)

class ModerateForm(ModeratorsOnlyMixin,
                   UpdateView):

    queryset = Problem.objects.unmoderated_problems().all()
    template_name = 'moderation/moderate-form.html'
    form_class = ProblemModerationForm

    # Standardise the context_object's name
    context_object_name = 'message'

    def get_success_url(self):
        return reverse('moderate-confirm')

class ModerateConfirm(ModeratorsOnlyMixin,
                      TemplateView):
    template_name = 'moderation/moderate-confirm.html'