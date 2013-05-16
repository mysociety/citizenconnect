import django_tables2 as tables

from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse
from django.utils.text import Truncator

from issues.table_columns import BreachAndEscalationColumn


class NationalSummaryTable(tables.Table):

    def __init__(self, *args, **kwargs):
        self.cobrand = kwargs.pop('cobrand')
        super(NationalSummaryTable, self).__init__(*args, **kwargs)

    name = tables.Column(verbose_name='Provider name',
                         attrs={'th': {'class': 'table__first'},
                                'td': {'class': 'table__first'}})
    week = tables.Column(verbose_name='Last 7 days')
    four_weeks = tables.Column(verbose_name='Last 4 weeks')
    six_months = tables.Column(verbose_name='Last 6 months')
    all_time = tables.Column(verbose_name='All time')
    average_time_to_acknowledge = tables.TemplateColumn(verbose_name='Average time to acknowledge (days)',
                                                        template_name='organisations/includes/time_interval_column.html')
    average_time_to_address = tables.TemplateColumn(verbose_name='Average time to address (days)',
                                                    template_name='organisations/includes/time_interval_column.html')
    happy_service = tables.TemplateColumn(verbose_name='% Happy with service',
                                          template_name="organisations/includes/percent_column.html")
    happy_outcome = tables.TemplateColumn(verbose_name='% Happy with outcome',
                                          template_name="organisations/includes/percent_column.html")
    average_recommendation_rating = tables.TemplateColumn(verbose_name='Average recommendation rating (out of 5)',
                                                          template_name='organisations/includes/rounded_column.html')

    def render_name(self, record):
        url = self.reverse_to_org_summary(record['ods_code'])
        return mark_safe('''<a href="%s">%s</a>''' % (url, record['name']))

    def reverse_to_org_summary(self, ods_code):
        return reverse(
            'public-org-summary',
            kwargs={'ods_code': ods_code, 'cobrand': self.cobrand}
        )

    class Meta:
        order_by = ('name',)


class PrivateNationalSummaryTable(NationalSummaryTable):

    def reverse_to_org_summary(self, ods_code):
        return reverse(
            'private-org-summary',
            kwargs={'ods_code': ods_code}
        )


class BaseProblemTable(tables.Table):
    """
    Base class for functionality _all_ tables of problems need
    """

    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by='id',
                                     attrs={'td': {'class': 'problem-table__heavy-text'}})
    created = tables.DateTimeColumn(verbose_name="Received",
                                    attrs={'td': {'class': 'problem-table__light-text'}})
    category = tables.Column(verbose_name='Category', orderable=False)

    # The accessor might be changed to private_summary on private pages
    summary = tables.Column(verbose_name='Snippet',
                            orderable=False,
                            accessor="summary",
                            attrs={'td': {'class': 'problem-table__light-text'}})

    # Will only be made visible on private pages
    breach_and_escalation = BreachAndEscalationColumn(visible=False)

    def __init__(self, *args, **kwargs):
        self.private = kwargs.pop('private')
        if self.private:
            self.base_columns['summary'].accessor = 'private_summary'
            self.base_columns['breach_and_escalation'].visible = True
        else:
            self.cobrand = kwargs.pop('cobrand')
            self.base_columns['summary'].accessor = 'summary'
            self.base_columns['breach_and_escalation'].visible = False

        super(BaseProblemTable, self).__init__(*args, **kwargs)

    def render_summary_as_response_link(self, record):
        response_link = self.row_href(record)
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(response_link, conditional_escape(record.private_summary)))

    def render_summary_as_public_link(self, record):
        detail_link = self.row_href(record)
        return mark_safe('<a href="{0}">{1} <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(detail_link, conditional_escape(record.summary)))

    def row_classes(self, record):
        try:
            super_row_classes = super(BaseProblemTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    def row_href(self, record):
        """Return an href for the given row

        Where we link to depends on whether this is public or private
        """

        if self.private:
            return reverse('response-form', kwargs={'pk': record.id})
        else:
            # self.cobrand might not be set
            try:
                cobrand = self.cobrand or 'choices'
            except AttributeError:
                cobrand = 'choices'
            return reverse('problem-view', kwargs={'pk': record.id, 'cobrand': cobrand})

    class Meta:
        attrs = {'class': 'problem-table problem-table--expanded'}


class ProblemTable(BaseProblemTable):
    """
    A table for an overview of public or private lists of problems related to a provider.
    Explicitly not for dashboards, where action related to those problems
    is implied or the primary focus.
    """
    happy_service = tables.TemplateColumn(verbose_name='Service',
                                          template_name="organisations/includes/boolean_column.html",
                                          orderable=False)
    happy_outcome = tables.TemplateColumn(verbose_name='Outcome',
                                          template_name="organisations/includes/boolean_column.html",
                                          orderable=False)
    status = tables.Column()

    split_columns = True

    def render_summary(self, record):
        if self.private:
            # Even though this action is not implied, it's still good usability
            # to link to what the private viewer will most likely want to do
            # with this problem
            return self.render_summary_as_response_link(record)
        elif record.public:
            return self.render_summary_as_public_link(record)
        else:
            return conditional_escape(record.summary)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'created',
                    'status',
                    'category',
                    'happy_service',
                    'happy_outcome',
                    'summary',
                    'breach_and_escalation')


class ExtendedProblemTable(ProblemTable):
    """
    Like ProblemTable but for organisations where has_services and
    has_time_limits are true meaning we show extra stats
    """
    service = tables.Column(verbose_name='Department', orderable=False)
    time_to_acknowledge = tables.TemplateColumn(verbose_name='Acknowledge',
                                                template_name='organisations/includes/time_interval_column.html',
                                                orderable=False)
    time_to_address = tables.TemplateColumn(verbose_name='Address',
                                            template_name='organisations/includes/time_interval_column.html',
                                            orderable=False)
    resolved = tables.DateTimeColumn(verbose_name="Resolved")

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'created',
                    'status',
                    'resolved',
                    'category',
                    'service',
                    'time_to_acknowledge',
                    'time_to_address',
                    'happy_service',
                    'happy_outcome',
                    'summary',
                    'breach_and_escalation')


class ProblemDashboardTable(BaseProblemTable):
    """
    A base Table class for all the different dashboards which show
    lists of problems. Quite similar to ProblemTable and ExtendedProblemTable
    but geared towards acting on problems, so not including satisfaction stats etc
    and always assuming a private context
    """

    service = tables.Column(verbose_name="Service", orderable=False)

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        kwargs['private'] = True
        super(ProblemDashboardTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}
        sequence = ('reference_number',
                    'created',
                    'category',
                    'service',
                    'summary')


class EscalationDashboardTable(ProblemDashboardTable):
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name')

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}
        sequence = ('reference_number',
                    'provider_name',
                    'created',
                    'service',
                    'category',
                    'summary')


class BreachTable(ProblemTable):
    """
    Annoyingly quite like ProblemTable, but with provider_name in as well
    """
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name')

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        self.private = True
        super(BreachTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'provider_name',
                    'created',
                    'status',
                    'category',
                    'happy_service',
                    'happy_outcome',
                    'summary')
        split_columns = True


class ReviewTable(tables.Table):
    """
    Displays reviews that have been pulled back from the API for a given
    organisation.
    """

    api_posting_id = tables.Column(verbose_name='Ref',
                                   attrs={'td': {'class': 'problem-table__heavy-text'}})
    api_published = tables.DateColumn(verbose_name='Received Date',
                                  attrs={'td': {'class': 'problem-table__light-text'}})

    # TODO: There must be a better way to get the Friends and Family rating.
    # TODO: Change this to be a TemplateColumn once the ratings are merged.
    rating = tables.Column(verbose_name='Rating', accessor='ratings.all.0.score')

    content = tables.Column(verbose_name='Review', orderable=False)

    def render_content(self, value):
        return Truncator(value).words(20)

    def row_classes(self, record):
        try:
            super_row_classes = super(ReviewTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}
