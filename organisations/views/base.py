# Standard imports
import json
import re
from ukpostcodeutils.validation import is_valid_postcode, is_valid_partial_postcode

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
from geocoder.models import Place

from .. import auth
from ..auth import (user_in_group,
                    user_is_superuser,
                    user_can_access_national_escalation_dashboard,
                    user_can_access_private_national_summary,
                    user_is_escalation_body)
from ..models import Organisation, SuperuserLogEntry
from ..forms import OrganisationFinderForm, FilterForm
from ..lib import interval_counts
from ..tables import (NationalSummaryTable,
                      PrivateNationalSummaryTable,
                      ProblemDashboardTable,
                      BreachTable)
from ..templatetags.organisation_extras import formatted_time_interval, percent


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


class FilterFormMixin(FormMixin):
    """
    Mixin for views which have a filter form
    """
    form_class = FilterForm

    # The flags filter lets you choose the bool field to filter as true. This
    # tuple is used to check that only expected values are filtered on.
    allowed_flag_filters = ('breach', 'formal_complaint')

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
            if name == 'organisation':
                filtered_queryset = filtered_queryset.filter(organisation=value)
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
                filtered_queryset = filtered_queryset.filter(organisation__parent__ccgs__id__exact=value)
            if name == 'flags' and value in self.allowed_flag_filters:
                args = {value: True}
                filtered_queryset = filtered_queryset.filter(**args)

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

        problem_filters = self.translate_flag_filters(problem_filters)

        return (problem_filters, organisation_filters)

    def translate_flag_filters(self, problem_filters):
        # For the flags translate the value of the flag to a bool filter for that field
        if problem_filters.get('flags'):
            flag_value = problem_filters['flags']
            del problem_filters['flags']
            if flag_value in self.allowed_flag_filters:
                problem_filters[flag_value] = True
        return problem_filters


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
        # Turn off the various flag filters
        kwargs['with_flags'] = False
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(Map, self).get_context_data(**kwargs)

        problem_filters, organisation_filters = self.interval_count_filters(context['selected_filters'])

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

        # Load all the organisations to use for the name select
        context['name_search_organisations'] = Organisation.objects.all().only('id', 'name').order_by('name')

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


class MapOrganisationCoords(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(MapOrganisationCoords, self).get_context_data(**kwargs)
        organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        org_data = {'lat': organisation.point.y, 'lon': organisation.point.x}
        context['organisation'] = json.dumps(org_data)
        return context

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(context['organisation'], content_type='application/json', **response_kwargs)


class MapSearch(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(MapSearch, self).get_context_data()

        term = self.request.GET.get('term', '')

        if len(term):
            to_serialize = []

            # Check if the term is a postcode
            postcode = re.sub('\s+', '', term.upper())
            if is_valid_postcode(postcode) or is_valid_partial_postcode(postcode):
                pass # TODO: return co-ordinates for this postcode from mapit

            organisations = Organisation.objects.filter(name__icontains=term)

            for obj in organisations[:8]:
                to_serialize.append({
                    "id":   obj.ods_code,
                    "text": obj.name,
                    "type": "organisation",
                    "lat":  obj.point.y,
                    "lon":  obj.point.x,
                });

            places = Place.objects.filter(name__istartswith=term)
            places = places.order_by('name')

            for obj in places[:8]:
                to_serialize.append({
                    "id":   obj.id,
                    "text": obj.context_name,
                    "type": "place",
                    "lat":  obj.centre.y,
                    "lon":  obj.centre.x,
                });

            context['results'] = to_serialize
        else:
            context['results'] = []


        return context

    def render_to_response(self, context, **kwargs):

        json_string = json.dumps(context['results'], sort_keys=True, indent=4)

        kwargs['content_type'] = 'application/json'
        return HttpResponse(json_string, **kwargs)


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
        self.enforce_access(request.user)
        return super(PrivateNationalSummary, self).dispatch(request, *args, **kwargs)

    def enforce_access(self, user):
        if not user_can_access_private_national_summary(user):
            raise PermissionDenied()

    def get_context_data(self, **kwargs):

        # default the cobrand
        if 'cobrand' not in kwargs:
            kwargs['cobrand'] = None

        context = super(PrivateNationalSummary, self).get_context_data(**kwargs)

        # Determine if we should show the page as part of some tabbed navigation
        if user_in_group(self.request.user, auth.CUSTOMER_CONTACT_CENTRE):
            context['show_tabs'] = True
            context['tabs_template'] = 'organisations/includes/escalation_tabs.html'

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

    # CCG users get their own problem dashboard
    elif user_in_group(user, auth.CCG):
        if user.ccgs.count() == 1:
            ccg = user.ccgs.all()[0]
            return HttpResponseRedirect(reverse('ccg-dashboard', kwargs={'code': ccg.code}))

    # Customer contact centre users go to the escalation dashboard
    elif user_in_group(user, auth.CUSTOMER_CONTACT_CENTRE):
        return HttpResponseRedirect(reverse('escalation-dashboard'))

    # Moderators go to the moderation queue
    elif user_in_group(user, auth.CASE_HANDLERS):
        return HttpResponseRedirect(reverse('moderate-home'))

    elif user_in_group(user, auth.SECOND_TIER_MODERATORS):
        return HttpResponseRedirect(reverse('second-tier-moderate-home'))

    # Organisation Parents
    elif user_in_group(user, auth.ORGANISATION_PARENTS):
        if user.organisation_parents.count() == 1:
            organisation_parent = user.organisation_parents.all()[0]
            return HttpResponseRedirect(reverse('org-parent-dashboard', kwargs={'code': organisation_parent.code}))

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
