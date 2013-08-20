from django.views.generic import TemplateView, UpdateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from django_tables2 import RequestConfig
from extra_views import UpdateWithInlinesView, InlineFormSet, NamedFormsetsMixin

# App imports
from issues.models import Problem
from organisations.auth import enforce_moderation_access_check, enforce_second_tier_moderation_access_check
from responses.models import ProblemResponse

from .forms import ProblemModerationForm, ProblemResponseInlineFormSet, ProblemSecondTierModerationForm
from issues.forms import LookupForm
from .tables import ModerationTable, SecondTierModerationTable


class ModeratorsOnlyMixin(object):
    """
    Mixin to protect views to only allow moderators to access them
    """

    def dispatch(self, request, *args, **kwargs):
        enforce_moderation_access_check(request.user)
        return super(ModeratorsOnlyMixin, self).dispatch(request, *args, **kwargs)


class SecondTierModeratorsOnlyMixin(object):
    """
    Mixin to protect views to only allow second tier moderators to access them
    """

    def dispatch(self, request, *args, **kwargs):
        enforce_second_tier_moderation_access_check(request.user)
        return super(SecondTierModeratorsOnlyMixin, self).dispatch(request, *args, **kwargs)


class ModerationTableMixin(object):

    def add_table_to_context(self, context, table_type):
        # Setup a table for the problems
        issue_table = table_type(context['issues'])
        RequestConfig(self.request, paginate={'per_page': 25}).configure(issue_table)
        context['table'] = issue_table
        context['page_obj'] = context['table'].page
        return context


class ModerationConfirmationMixin(object):

    def get_context_data(self, **kwargs):
        context = super(ModerationConfirmationMixin, self).get_context_data(**kwargs)
        context['home_link'] = self.home_link
        return context


class ModerateHome(ModeratorsOnlyMixin,
                   ModerationTableMixin,
                   TemplateView):
    template_name = 'moderation/moderate_home.html'

    def get_context_data(self, **kwargs):
        # Get all the unmoderated problems
        context = super(ModerateHome, self).get_context_data(**kwargs)
        context['issues'] = Problem.objects.unmoderated_problems().order_for_moderation_table()
        context['title'] = "Moderation"
        context['private'] = True
        self.add_table_to_context(context, ModerationTable)
        return context


class SecondTierModerateHome(SecondTierModeratorsOnlyMixin,
                             ModerationTableMixin,
                             TemplateView):
    template_name = 'moderation/second_tier_moderate_home.html'

    def get_context_data(self, **kwargs):
        # Get all the problems flagged for second tier moderation
        context = super(SecondTierModerateHome, self).get_context_data(**kwargs)
        context['issues'] = Problem.objects.problems_requiring_second_tier_moderation().order_for_moderation_table()
        context['title'] = "Second Tier Moderation"
        context['private'] = True
        self.add_table_to_context(context, SecondTierModerationTable)
        return context


class ModerateLookup(ModeratorsOnlyMixin,
                     FormView):
    template_name = 'moderation/moderate_lookup.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        moderate_url = reverse("moderate-form", kwargs={'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(moderate_url)


class ProblemResponseInline(InlineFormSet):
    model = ProblemResponse
    can_delete = True
    max_num = 0
    fields = ('response',)


class ModerateForm(ModeratorsOnlyMixin,
                   UpdateWithInlinesView,
                   NamedFormsetsMixin):

    model = Problem
    template_name = 'moderation/moderate_form.html'
    form_class = ProblemModerationForm

    # Standardise the context_object's name
    context_object_name = 'issue'

    # Settings for the inline formsets
    inlines = [ProblemResponseInline]
    inlines_names = ['response_forms']

    def get_form_kwargs(self):
        # Add the request to the form's kwargs
        kwargs = super(ModerateForm, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse('moderate-confirm')


class SecondTierModerateForm(SecondTierModeratorsOnlyMixin,
                             UpdateView):
    queryset = Problem.objects.problems_requiring_second_tier_moderation().all()
    template_name = 'moderation/second_tier_moderate_form.html'
    form_class = ProblemSecondTierModerationForm
    # Standardise the context_object's name
    context_object_name = 'issue'

    def get_form_kwargs(self):
        # Add the request to the form's kwargs
        kwargs = super(SecondTierModerateForm, self).get_form_kwargs()
        kwargs.update({
            'request': self.request
        })
        return kwargs

    def get_success_url(self):
        return reverse('second-tier-moderate-confirm')

    def get_context_data(self, **kwargs):
        context = super(SecondTierModerateForm, self).get_context_data(**kwargs)
        context['issue'] = Problem.objects.get(pk=self.kwargs['pk'])
        return context


class ModerateConfirm(ModeratorsOnlyMixin,
                      ModerationConfirmationMixin,
                      TemplateView):
    template_name = 'moderation/moderate_confirm.html'
    home_link = 'moderate-home'


class SecondTierModerateConfirm(SecondTierModeratorsOnlyMixin,
                                ModerationConfirmationMixin,
                                TemplateView):
    template_name = 'moderation/moderate_confirm.html'
    home_link = 'second-tier-moderate-home'
