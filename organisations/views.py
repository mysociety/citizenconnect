# Standard imports
import json

# Django imports
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse, resolve
from django.core.exceptions import PermissionDenied
from django_tables2 import RequestConfig
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Polygon

# App imports
from citizenconnect.shortcuts import render
from issues.models import Problem

import auth
from .auth import (user_in_group,
                   user_in_groups,
                   user_is_superuser,
                   enforce_organisation_access_check,
                   enforce_trust_access_check,
                   user_can_access_escalation_dashboard,
                   user_can_access_private_national_summary,
                   user_is_escalation_body)
from .models import Organisation, SuperuserLogEntry, Trust
from .forms import OrganisationFinderForm, FilterForm, OrganisationFilterForm
from .lib import interval_counts
from .tables import (NationalSummaryTable,
                     PrivateNationalSummaryTable,
                     ProblemTable,
                     ExtendedProblemTable,
                     ProblemDashboardTable,
                     EscalationDashboardTable,
                     BreachTable)
from .templatetags.organisation_extras import formatted_time_interval, percent


class PrivateViewMixin(object):
    """
    Mixin for views which need access to a context variable indicating whether the view
    is being accessed in a private context, only accessible to logged-in users.
    """

    def get_context_data(self, **kwargs):
        context = super(PrivateViewMixin, self).get_context_data(**kwargs)
        if 'private' in kwargs and kwargs['private'] is True:
            context['private'] = True
        else:
            context['private'] = False
        return context


class OrganisationAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    organisation, such as problem forms."""

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        return super(OrganisationAwareViewMixin, self).dispatch(request, *args, **kwargs)

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation
        # Check that the user can access the organisation if this is private
        if context['private']:
            enforce_organisation_access_check(context['organisation'], self.request.user)
        return context


class TrustAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    trust, such as trust dashboards."""

    def dispatch(self, request, *args, **kwargs):
        # Set trust here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.trust = Trust.objects.get(code=kwargs['code'])
        return super(TrustAwareViewMixin, self).dispatch(request, *args, **kwargs)

    # Get the organisation name
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(TrustAwareViewMixin, self).get_context_data(**kwargs)
        context['trust'] = self.trust
        # Check that the user can access the trust if this is private
        if context['private']:
            enforce_trust_access_check(context['trust'], self.request.user)
        return context


class FilterFormMixin(FormMixin):
    """
    Mixin for views which have a filter form
    """
    form_class = FilterForm

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        # Note: we call this to get a cleaned_data dict, which we then
        # pass on into the context for use in filtering, but we don't
        # care if it fails, because then it won't go into the context
        # and the views can just ignore any duff selections
        form.is_valid()
        kwargs['form'] = form
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_form_kwargs(self):
        # Pass form kwargs from GET instead of POST
        kwargs = {'initial': self.get_initial()}
        if self.request.GET:
            kwargs['data'] = self.request.GET
        if 'private' in self.kwargs and self.kwargs['private'] is True:
            kwargs['private'] = True
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(FilterFormMixin, self).get_context_data(**kwargs)
        form = context['form']
        selected_filters = {}
        if hasattr(form, 'cleaned_data'):
            for name, value in form.cleaned_data.items():
                # The hasattr deals with ModelChoiceFields, where cleaned_data
                # will return a model instance, not a single value, but code
                # which uses it wants only the id
                if value is not None and value != '' and hasattr(value, 'id'):
                    selected_filters[name] = value.id
                elif value is not None and value != '':
                    selected_filters[name] = value
        context['selected_filters'] = selected_filters
        return context

    def filter_problems(self, filters, queryset):
        """
        Filter a queryset of problems by the supplied filters
        """
        filtered_queryset = queryset
        for name, value in filters.items():
            if name == 'status':
                filtered_queryset = filtered_queryset.filter(status=value)
            if name == 'category':
                filtered_queryset = filtered_queryset.filter(category=value)
            if name == 'organisation_type':
                filtered_queryset = filtered_queryset.filter(organisation__organisation_type=value)
            if name == 'service_code':
                filtered_queryset = filtered_queryset.filter(service__service_code=value)
            if name == 'service_id':
                filtered_queryset = filtered_queryset.filter(service__id=value)
            if name == 'ccg':
                filtered_queryset = filtered_queryset.filter(organisation__trust__ccgs__id__exact=value)
            if name == 'breach':
                filtered_queryset = filtered_queryset.filter(breach=value)
        return filtered_queryset

    def interval_count_filters(self, filters):
        # Build dictionaries of filters in the format we can pass
        # into interval_counts to filter the problems and organisations
        problem_filters = filters.copy()

        # move the filters that specifically apply to organisations
        # to another dictionary
        organisation_attrs = ['ccg', 'organisation_type']
        organisation_filters = {}
        for organisation_attr in organisation_attrs:
            value = problem_filters.pop(organisation_attr, None)
            if value is not None:
                organisation_filters[organisation_attr] = value

        if problem_filters.get('status') is not None:
            # ignore a filter request for a status that isn't permitted
            if not problem_filters['status'] in self.permitted_statuses:
                del problem_filters['status']

        if problem_filters.get('status') is None:
            # by default the status should filter for the permitted statuses
            problem_filters['status'] = tuple(self.permitted_statuses)

        return (problem_filters, organisation_filters)


class Map(FilterFormMixin,
          TemplateView):
    template_name = 'organisations/map.html'
    permitted_statuses = Problem.VISIBLE_STATUSES
    london_area = Polygon.from_bbox((-0.7498168945312499, 51.291123547147215, 0.56854248046875, 51.71852107186864))

    def get_form_kwargs(self):
        kwargs = super(Map, self).get_form_kwargs()
        # Turn off ccg filter
        kwargs['with_ccg'] = False
        # Turn off department filter
        kwargs['with_service_code'] = False
        # Turn off breach filter
        kwargs['with_breach'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Map, self).get_context_data(**kwargs)

        problem_filters, organisation_filters = self.interval_count_filters(context['selected_filters'])

        # Show counts for moderated, published problems
        problem_filters['moderated'] = Problem.MODERATED
        problem_filters['publication_status'] = Problem.PUBLISHED

        organisations_within_map_bounds_ids = [col.id for col in self.organisations_within_map_bounds()]
        organisations_list = []

        if len(organisations_within_map_bounds_ids):
            # Query for summary counts for the organisations within the map bounds.
            organisation_filters['organisation_ids'] = tuple(organisations_within_map_bounds_ids)

            organisations_problem_data = interval_counts(problem_filters=problem_filters,
                                                 organisation_filters=organisation_filters,
                                                 extra_organisation_data=['coords', 'type', 'average_recommendation_rating'],
                                                 data_intervals=['all_time_open', 'all_time_closed'],
                                                 average_fields=['time_to_address'],
                                                 boolean_fields=['happy_outcome'])
            organisations_review_data = interval_counts(organisation_filters=organisation_filters,
                                                        data_type='reviews')

            for problem_data, review_data in zip(organisations_problem_data, organisations_review_data):
                organisations_list.append(dict(problem_data.items() + review_data.items()))

        for org_data in organisations_list:
            org_data['url'] = reverse('public-org-summary',
                                      kwargs={'ods_code': org_data['ods_code'],
                                              'cobrand': self.kwargs['cobrand']})
            org_data['average_time_to_address'] = formatted_time_interval(org_data['average_time_to_address'])
            org_data['happy_outcome'] = percent(org_data['happy_outcome'])
        # Make it into a JSON string
        context['organisations'] = json.dumps(organisations_list)

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Overriden render_to_response to return JSON if GET['format'] == 'json'
        and use the standard TemplateView method otherwise.
        """
        if self.request.GET.get('format') == 'json':
            return HttpResponse(context['organisations'],
                                content_type='application/json',
                                **response_kwargs)
        else:
            return super(Map, self).render_to_response(context, **response_kwargs)

    def organisations_within_map_bounds(self):
        """
        Get a QuerySet of all the organisations within the current map
        bounds, defaulting to the London area.
        """
        map_bounds = self.request.GET.getlist('bounds[]')

        if len(map_bounds):
            map_bounds = Polygon.from_bbox(tuple(map_bounds))
        else:
            map_bounds = self.london_area

        return Organisation.objects.filter(point__within=map_bounds)


class PickProviderBase(ListView):
    template_name = 'provider_results.html'
    form_template_name = 'pick_provider.html'
    result_link_url_name = 'public-org-summary'
    paginate_by = 10
    model = Organisation
    context_object_name = 'organisations'

    def __init__(self, *args, **kwargs):
        super(PickProviderBase, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PickProviderBase, self).get_context_data(**kwargs)

        try:
            context['title_text'] = self.title_text
        except AttributeError:
            pass

        try:
            context['form'] = self.form
        except AttributeError:
            pass

        return context

    def get(self, *args, **kwargs):
        super(PickProviderBase, self).get(*args, **kwargs)
        if self.request.GET:
            form = OrganisationFinderForm(self.request.GET)
            if form.is_valid():  # All validation rules pass
                context = self.get_context_data(object_list=self.object_list)
                context.update({'location': form.cleaned_data['location'],
                                'organisations': form.cleaned_data['organisations'],
                                'result_link_url_name': self.result_link_url_name,
                                'paginator': None,
                                'page_obj': None,
                                'is_paginated': False})
                self.queryset = form.cleaned_data['organisations']
                page_size = self.get_paginate_by(self.queryset)
                if page_size:
                    paginator, page, queryset, is_paginated = self.paginate_queryset(self.queryset, page_size)
                    context['paginator'] = paginator
                    context['page_obj'] = page
                    context['is_paginated'] = is_paginated
                    context['organisations'] = queryset
                    context['current_url'] = resolve(self.request.path_info).url_name
                return render(self.request, self.template_name, context)
            else:
                self.form = form
                return render(self.request, self.form_template_name, self.get_context_data(object_list=self.object_list))
        else:
            self.form = OrganisationFinderForm()
            return render(self.request, self.form_template_name, self.get_context_data(object_list=self.object_list))


class OrganisationPickProvider(PickProviderBase):
    pass


class OrganisationSummary(OrganisationAwareViewMixin,
                          FilterFormMixin,
                          TemplateView):
    template_name = 'organisations/organisation_summary.html'

    # Use an OrganisationFilterForm instead of a normal one
    form_class = OrganisationFilterForm

    def get_form_kwargs(self):
        kwargs = super(OrganisationSummary, self).get_form_kwargs()

        kwargs['organisation'] = self.organisation
        # Only show service_id if the organisation has services
        if not self.organisation.has_services():
            kwargs['with_service_id'] = False

        # We don't want a status filter
        kwargs['with_status'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(OrganisationSummary, self).get_context_data(**kwargs)

        organisation = context['organisation']

        # Load the user-selected filters from the form
        count_filters = context['selected_filters']

        # Figure out which statuses to calculate summary stats and lines in
        # the summary table from
        if context['private']:
            status_rows = Problem.STATUS_CHOICES
            volume_statuses = Problem.ALL_STATUSES
        else:
            status_rows = Problem.VISIBLE_STATUS_CHOICES
            volume_statuses = Problem.VISIBLE_STATUSES

        summary_stats_statuses = Problem.VISIBLE_STATUSES
        count_filters['status'] = tuple(volume_statuses)
        organisation_filters = {'organisation_id': organisation.id}
        context['problems_total'] = interval_counts(problem_filters=count_filters,
                                                    organisation_filters=organisation_filters)
        count_filters['status'] = tuple(summary_stats_statuses)
        context['problems_summary_stats'] = interval_counts(problem_filters=count_filters,
                                                            organisation_filters=organisation_filters)
        status_list = []
        for status, description in status_rows:
            count_filters['status'] = (status,)
            status_counts = interval_counts(problem_filters=count_filters,
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


class OrganisationProblems(OrganisationAwareViewMixin,
                           FilterFormMixin,
                           TemplateView):
    template_name = 'organisations/organisation_problems.html'

    form_class = OrganisationFilterForm

    def get_form_kwargs(self):
        kwargs = super(OrganisationProblems, self).get_form_kwargs()

        kwargs['organisation'] = self.organisation
        # Only show service_id if the organisation has services
        if not self.organisation.has_services():
            kwargs['with_service_id'] = False

        return kwargs

    def get_problems(self, organisation, private):
        if private:
            return organisation.problem_set.all()
        else:
            return organisation.problem_set.all_moderated_published_problems()

    def get_context_data(self, **kwargs):
        context = super(OrganisationProblems, self).get_context_data(**kwargs)

        # Get a queryset of issues and apply any filters to them
        problems = self.get_problems(context['organisation'], context['private'])
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Build a table
        table_args = {'private': context['private']}
        if not context['private']:
            table_args['cobrand'] = kwargs['cobrand']

        if context['organisation'].has_services() and context['organisation'].has_time_limits():
            problem_table = ExtendedProblemTable(filtered_problems, **table_args)
        else:
            problem_table = ProblemTable(filtered_problems, **table_args)

        RequestConfig(self.request, paginate={'per_page': 8}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page
        return context


class Summary(FilterFormMixin, PrivateViewMixin, TemplateView):
    template_name = 'organisations/summary.html'
    permitted_statuses = Problem.VISIBLE_STATUSES
    summary_table_class = NationalSummaryTable

    def get_context_data(self, **kwargs):
        context = super(Summary, self).get_context_data(**kwargs)

        problem_filters, organisation_filters = self.interval_count_filters(context['selected_filters'])
        threshold = None
        if settings.SUMMARY_THRESHOLD:
            threshold = settings.SUMMARY_THRESHOLD
        organisation_rows = self.get_interval_counts(problem_filters=problem_filters,
                                                     organisation_filters=organisation_filters,
                                                     threshold=threshold)
        organisations_table = self.summary_table_class(organisation_rows,
                                                       cobrand=kwargs['cobrand'])

        RequestConfig(self.request, paginate={"per_page": 8}).configure(organisations_table)
        context['table'] = organisations_table
        context['page_obj'] = organisations_table.page

        # If a specific interval is requested, we need to pull out that column
        # so that the template can know to alter the heading which covers all
        # of those intervals to show the right sorting link
        problems_interval = self.request.GET.get('problems_interval', 'all_time')
        if problems_interval in organisations_table.columns:
            context['problems_sort_column'] = organisations_table.columns[problems_interval]
        else:
            context['problems_sort_column'] = organisations_table.columns['all_time']
        reviews_interval = self.request.GET.get('reviews_interval', 'reviews_all_time')
        if reviews_interval in organisations_table.columns:
            context['reviews_sort_column'] = organisations_table.columns[reviews_interval]
        else:
            context['reviews_sort_column'] = organisations_table.columns['reviews_all_time']

        return context

    def get_interval_counts(self, problem_filters, organisation_filters, threshold):
        organisation_problem_data = interval_counts(problem_filters=problem_filters,
                                                    organisation_filters=organisation_filters)
        organisation_review_data = interval_counts(organisation_filters=organisation_filters,
                                                   data_type='reviews',
                                                   extra_organisation_data=['average_recommendation_rating'])
        organisation_data = []
        if threshold:
            interval, cutoff = threshold
        for problem_data, review_data in zip(organisation_problem_data, organisation_review_data):
            if (not threshold) or (problem_data[interval] >= cutoff or
                review_data['reviews_' + interval] >= cutoff):
                organisation_data.append(dict(problem_data.items() + review_data.items()))

        return organisation_data


class PrivateNationalSummary(Summary):
    template_name = 'organisations/national_summary.html'
    permitted_statuses = Problem.ALL_STATUSES
    summary_table_class = PrivateNationalSummaryTable

    def dispatch(self, request, *args, **kwargs):

        if not user_can_access_private_national_summary(request.user):
            raise PermissionDenied()

        return super(PrivateNationalSummary, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):

        # default the cobrand
        if 'cobrand' not in kwargs:
            kwargs['cobrand'] = None

        context = super(PrivateNationalSummary, self).get_context_data(**kwargs)

        # Determine if we should show the page as part of some tabbed navigation
        if user_is_escalation_body(self.request.user):
            context['show_escalation_tabs'] = True

        return context

    def get_interval_counts(self, problem_filters, organisation_filters, threshold):

        user = self.request.user

        # If the user is in a CCG Group then filter results to that CCG.
        if user_in_group(user, auth.CCG):

            # If the user has assigned CCGs then limit to those. If they have
            # none then throw an exception (they should not have gotten past user_can_access_private_national_summary)
            ccgs = user.ccgs.all()
            if not len(ccgs):
                raise Exception("CCG group user '{0}' has no ccgs - they should not have gotten past check in dispatch".format(user))
            ccg_ids = [ccg.id for ccg in ccgs]
            # Don't remove the ccg filter they've added if it's in their ccgs
            selected_ccg = organisation_filters.get('ccg')
            if not selected_ccg or not int(selected_ccg) in ccg_ids:
                organisation_filters['ccg'] = tuple(ccg_ids)

        return super(PrivateNationalSummary, self).get_interval_counts(problem_filters=problem_filters,
                                                                     organisation_filters=organisation_filters,
                                                                     threshold=threshold)


class OrganisationDashboard(OrganisationAwareViewMixin,
                            TemplateView):
    template_name = 'organisations/dashboard.html'

    def get_context_data(self, **kwargs):
        # Get all the problems
        context = super(OrganisationDashboard, self).get_context_data(**kwargs)

        # Get the models related to this organisation, and let the db sort them
        problems = context['organisation'].problem_set.open_unescalated_problems()
        problems_table = ProblemDashboardTable(problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problems_table)
        context['table'] = problems_table
        context['page_obj'] = problems_table.page
        organisation_filters = {'organisation_id': context['organisation'].id}
        context['problems_total'] = interval_counts(organisation_filters=organisation_filters)
        return context


@login_required
def login_redirect(request):
    """
    View function to redirect a logged in user to the right url after logging in.
    Allows users to have an effective "homepage" which they go to automatically
    after logging in. Uses their user group to determine what is the right page.
    """

    user = request.user

    # NHS Super users get a special map page
    if user_in_group(user, auth.NHS_SUPERUSERS):
        return HttpResponseRedirect(reverse('private-national-summary'))

    # CCG, and customer contact centre users go to the escalation dashboard
    elif user_in_groups(user, [auth.CCG, auth.CUSTOMER_CONTACT_CENTRE]):
        return HttpResponseRedirect(reverse('escalation-dashboard'))

    # Moderators go to the moderation queue
    elif user_in_group(user, auth.CASE_HANDLERS):
        return HttpResponseRedirect(reverse('moderate-home'))

    elif user_in_group(user, auth.SECOND_TIER_MODERATORS):
        return HttpResponseRedirect(reverse('second-tier-moderate-home'))

    # Trusts
    elif user_in_group(user, auth.TRUSTS):
        # For now, trust users go to their first org's dashboard - eventually they
        # will get their own special dashboard with all the orgs on it
        if user.trusts.count() == 1:
            trust = user.trusts.all()[0]
            organisation = trust.organisations.all()[0]
            return HttpResponseRedirect(reverse('org-dashboard', kwargs={'ods_code': organisation.ods_code}))

    # Anyone else goes to the normal homepage
    return HttpResponseRedirect(reverse('home', kwargs={'cobrand': 'choices'}))


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


class EscalationDashboard(FilterFormMixin, TemplateView):

    template_name = 'organisations/escalation_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not user_can_access_escalation_dashboard(request.user):
            raise PermissionDenied()
        return super(EscalationDashboard, self).dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(EscalationDashboard, self).get_form_kwargs()

        # Turn off the ccg filter if the user is a ccg
        user = self.request.user
        if not user_is_superuser(user) and not user_in_group(user, auth.CUSTOMER_CONTACT_CENTRE):
            kwargs['with_ccg'] = False
            kwargs['organisations'] = Organisation.objects.filter(trust__in=user.trusts.all())

        # Turn off status too, because all problems on this dashboard have
        # a status of Escalated
        kwargs['with_status'] = False

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EscalationDashboard, self).get_context_data(**kwargs)

        problems = Problem.objects.open_escalated_problems()
        user = self.request.user

        # Restrict problem queryset for non-superuser users (i.e. CCG users)
        if not user_is_superuser(user) and not user_in_group(user, auth.CUSTOMER_CONTACT_CENTRE):
            problems = problems.filter(organisation__trust__escalation_ccg__in=(user.ccgs.all()),
                                       commissioned=Problem.LOCALLY_COMMISSIONED)
        # Restrict problem queryset for non-CCG users (i.e. Customer Contact Centre)
        elif not user_is_superuser(user) and not user_in_group(user, auth.CCG):
            problems = problems.filter(commissioned=Problem.NATIONALLY_COMMISSIONED)

        # Apply form filters on top of this
        filtered_problems = self.filter_problems(context['selected_filters'], problems)

        # Setup a table for the problems
        problem_table = EscalationDashboardTable(filtered_problems)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        return context


class EscalationBreaches(TemplateView):

    template_name = 'organisations/escalation_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        if not user_can_access_escalation_dashboard(request.user):
            raise PermissionDenied()
        return super(EscalationBreaches, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EscalationBreaches, self).get_context_data(**kwargs)
        problems = Problem.objects.open_problems().filter(breach=True)

        # Restrict problem queryset for non-superuser users (i.e. CCG users)
        user = self.request.user
        if not user_is_superuser(user) and not user_in_group(user, auth.CUSTOMER_CONTACT_CENTRE):
            problems = problems.filter(organisation__trust__escalation_ccg__in=(user.ccgs.all()))
        # Everyone else see's all breaches

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        return context


class TrustBreaches(TrustAwareViewMixin,
                    TemplateView):

    template_name = 'organisations/organisation_breaches.html'

    def dispatch(self, request, *args, **kwargs):
        return super(TrustBreaches, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrustBreaches, self).get_context_data(**kwargs)
        problems = Problem.objects.open_problems().filter(breach=True, organisation__trust=context['trust'])

        # Setup a table for the problems
        problem_table = BreachTable(problems, private=True)
        RequestConfig(self.request, paginate={'per_page': 25}).configure(problem_table)
        context['table'] = problem_table
        context['page_obj'] = problem_table.page

        # These tables are always in the private context
        context['private'] = True

        return context
