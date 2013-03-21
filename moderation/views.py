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
from organisations.auth import user_in_group, user_is_superuser, user_in_groups

from .forms import LookupForm, ProblemModerationForm, ProblemResponseInlineFormSet
from .tables import ModerationTable, LegalModerationTable

class ModeratorsOnlyMixin(object):
    """
    Mixin to protect views to only allow moderators to access them
    """

    def dispatch(self, request, *args, **kwargs):
        if not user_is_superuser(request.user) and not user_in_group(request.user, auth.CASE_HANDLERS):
            raise PermissionDenied()
        else:
            return super(ModeratorsOnlyMixin, self).dispatch(request, *args, **kwargs)

class LegalModeratorsOnlyMixin(object):
    """
    Mixin to protect views to only allow legal moderators to access them
    """

    def dispatch(self, request, *args, **kwargs):
        if not user_is_superuser(request.user) and not user_in_groups(request.user,
                                                                      [auth.LEGAL_MODERATORS,
                                                                       auth.CASE_HANDLERS]):
            raise PermissionDenied()
        else:
            return super(LegalModeratorsOnlyMixin, self).dispatch(request, *args, **kwargs)

class ModerationTableView(object):

    def add_table_to_context(self, context, table_type):
        # Setup a table for the problems
        issue_table = table_type(context['issues'])
        RequestConfig(self.request, paginate={'per_page': 25}).configure(issue_table)
        context['table'] = issue_table
        context['page_obj'] = context['table'].page
        return context

class ModerateHome(ModeratorsOnlyMixin,
                   ModerationTableView,
                   TemplateView):
    template_name = 'moderation/moderate_home.html'

    def get_context_data(self, **kwargs):
        # Get all the unmoderated problems
        context = super(ModerateHome, self).get_context_data(**kwargs)
        context['issues'] = Problem.objects.unmoderated_problems().order_by("-created")
        context['title'] = "Moderation"
        self.add_table_to_context(context, ModerationTable)
        return context

class LegalModerateHome(LegalModeratorsOnlyMixin,
                        ModerationTableView,
                        TemplateView):
    template_name = 'moderation/moderate_home.html'

    def get_context_data(self, **kwargs):
        # Get all the problems flagged for legal moderation
        context = super(LegalModerateHome, self).get_context_data(**kwargs)
        context['issues'] = Problem.objects.all().filter(requires_legal_moderation=True).order_by("-created")
        context['title'] = "Legal Moderation"
        self.add_table_to_context(context, LegalModerationTable)
        return context

class ModerateLookup(ModeratorsOnlyMixin,
                     FormView):
    template_name = 'moderation/moderate_lookup.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        context = RequestContext(self.request)
        moderate_url = reverse("moderate-form", kwargs={'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(moderate_url)

class ModerateForm(ModeratorsOnlyMixin,
                   UpdateView):

    queryset = Problem.objects.all()
    template_name = 'moderation/moderate_form.html'
    form_class = ProblemModerationForm

    # Standardise the context_object's name
    context_object_name = 'issue'

    def get_success_url(self):
        return reverse('moderate-confirm')

    def get_context_data(self, **kwargs):
        context = super(ModerateForm, self).get_context_data(**kwargs)
        issue = Problem.objects.get(pk=self.kwargs['pk'])
        if self.request.POST:
            context['response_forms'] = ProblemResponseInlineFormSet(self.request.POST, instance=issue)
        else:
            context['response_forms'] = ProblemResponseInlineFormSet(instance=issue)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        if 'response_forms' in context:
            response_forms = context['response_forms']
            if response_forms.is_valid():
                self.object = form.save()
                response_forms.instance = self.object
                response_forms.save()
            else:
                return self.render_to_response(self.get_context_data(form=form))
        else:
            self.object = form.save()

        return HttpResponseRedirect(self.get_success_url())

class LegalModerateForm(LegalModeratorsOnlyMixin,
                        UpdateView):
    pass
class ModerateConfirm(ModeratorsOnlyMixin,
                      TemplateView):
    template_name = 'moderation/moderate_confirm.html'
