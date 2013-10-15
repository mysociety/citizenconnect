# Django imports
from django.http import Http404
from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.conf import settings

# App imports
from issues.models import Problem

from .. import auth
from ..auth import enforce_organisation_access_check, user_in_group
from ..models import Organisation
from ..forms import OrganisationFilterForm
from ..lib import interval_counts

from .base import PrivateViewMixin, PickProviderBase, FilterFormMixin


class OrganisationAwareViewMixin(PrivateViewMixin):
    """Mixin class for views which need to have a reference to a particular
    organisation, such as problem forms."""

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        try:
            self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        except Organisation.DoesNotExist:
            raise Http404
        return super(OrganisationAwareViewMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(OrganisationAwareViewMixin, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation
        # Check that the user can access the organisation if this is private
        if context['private']:
            enforce_organisation_access_check(context['organisation'], self.request.user)
        return context


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
        count_filters['status'] = tuple(summary_stats_statuses)
        count_filters = self.translate_flag_filters(count_filters)

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

        if context['private']:
            if user_in_group(self.request.user, auth.CCG):
                context['private_back_to_summaries_link'] = reverse('ccg-summary', kwargs={'code': self.request.user.ccgs.all()[0].code})
            elif user_in_group(self.request.user, auth.ORGANISATION_PARENTS):
                context['private_back_to_summaries_link'] = reverse('org-parent-summary', kwargs={'code': self.request.user.organisation_parents.all()[0].code})

        return context


class OrganisationSurveys(OrganisationAwareViewMixin, TemplateView):

    template_name = 'organisations/organisation_surveys.html'

    def get_context_data(self, **kwargs):
        context = super(OrganisationSurveys, self).get_context_data(**kwargs)

        organisation = context['organisation']

        context['survey_locations'] = settings.SURVEY_LOCATION_CHOICES

        context['surveys'] = []

        for location, location_label in context['survey_locations']:
            location_surveys = {}
            location_surveys['location_id'] = location
            location_surveys['location_name'] = location_label
            if organisation.surveys.filter(location=location).count() > 0:
                location_surveys['latest_survey'] = organisation.surveys.filter(location=location)[0]
                if organisation.surveys.filter(location=location).count() > 1:
                    location_surveys['previous_surveys'] = organisation.surveys.filter(location=location)[1:6]
                context['surveys'].append(location_surveys)

        return context
