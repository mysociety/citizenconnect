import django_tables2 as tables

from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse

from issues.models import Problem
from issues.table_columns import ReferenceNumberColumn


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

    reference_number = ReferenceNumberColumn(attrs={'th': {'class': 'table__first'},
                                                    'td': {'class': 'table__first'}})
    created = tables.DateTimeColumn(verbose_name="Received")
    category = tables.Column(verbose_name='Category', orderable=False)

    # The accessor might be changed to private_summary on private pages
    summary = tables.Column(verbose_name='Snippet', orderable=False, accessor="summary")

    def __init__(self, *args, **kwargs):
        self.private = kwargs.pop('private')
        if self.private:
            self.base_columns['summary'].accessor = 'private_summary'
        else:
            self.cobrand = kwargs.pop('cobrand')

        super(BaseProblemTable, self).__init__(*args, **kwargs)

    def render_summary_as_response_link(self, record):
        response_link = reverse("response-form", kwargs={'pk': record.id})
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(response_link, conditional_escape(record.private_summary)))

    def render_summary_as_public_link(self, record):
        # self.cobrand might not be set
        try:
            cobrand = self.cobrand or 'choices'
        except AttributeError:
            cobrand = 'choices'
        detail_link = reverse('problem-view', kwargs={'cobrand': cobrand, 'pk': record.id})
        return mark_safe('<a href="{0}">{1} <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(detail_link, conditional_escape(record.summary)))


class ProblemTable(BaseProblemTable):
    """
    A table for an overview of public or private lists of problems related to a provider.
    Explicitly not for dashboards, where action related to those problems
    is implied or the primary focus.
    """
    happy_service = tables.TemplateColumn(verbose_name='Happy with service',
                                          template_name="organisations/includes/boolean_column.html")
    happy_outcome = tables.TemplateColumn(verbose_name='Happy with outcome',
                                          template_name="organisations/includes/boolean_column.html")
    status = tables.Column()

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
                    'summary')


class ExtendedProblemTable(ProblemTable):
    """
    Like ProblemTable but for organisations where has_services and
    has_time_limits are true meaning we show extra stats
    """
    service = tables.Column(verbose_name='Department')
    time_to_acknowledge = tables.TemplateColumn(verbose_name='Time to acknowledge (days)',
                                                template_name='organisations/includes/time_interval_column.html')
    time_to_address = tables.TemplateColumn(verbose_name='Time to address (days)',
                                            template_name='organisations/includes/time_interval_column.html')
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
                    'summary')


class ProblemDashboardTable(BaseProblemTable):
    """
    A base Table class for all the different dashboards which show
    lists of problems. Quite similar to ProblemTable and ExtendedProblemTable
    but geared towards acting on problems, so not including satisfaction stats etc
    and always assuming a private context
    """

    reference_number = ReferenceNumberColumn(attrs={'th': {'class': 'table__first'},
                                                    'td': {'class': 'table__first  dashboard-table__heavy-text  dashboard-table__highlight'}})
    service = tables.Column(verbose_name="Service", orderable=False)

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        kwargs['private'] = True
        super(ProblemDashboardTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "dashboard-table"}
        sequence = ('reference_number',
                    'created',
                    'category',
                    'service',
                    'summary')


class EscalationDashboardTable(ProblemDashboardTable):
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name',
                                  attrs={'th': {'class': 'table__first'},
                                         'td': {'class': 'table__first'}})
    # Redefine this to tell it that it's not table__first anymore
    reference_number = ReferenceNumberColumn(attrs={'th': {'class': ''},
                                                    'td': {'class': ''}})

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('provider_name',
                    'reference_number',
                    'created',
                    'service',
                    'category',
                    'summary')


class BreachTable(ProblemTable):
    """
    Annoyingly quite like ProblemTable, but with provider_name in as well
    """
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name',
                                  attrs={'th': {'class': 'table__first'},
                                         'td': {'class': 'table__first'}})
    # Redefine this to tell it that it's not table__first anymore
    reference_number = ReferenceNumberColumn(attrs={'th': {'class': ''},
                                                    'td': {'class': ''}})

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        self.private = True
        super(BreachTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('provider_name',
                    'reference_number',
                    'created',
                    'status',
                    'category',
                    'happy_service',
                    'happy_outcome',
                    'summary')
