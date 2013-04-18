# encoding: utf-8

import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse

from issues.models import Problem

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

    def render_name(self, record):
        url = reverse("public-org-summary", kwargs={'ods_code': record['ods_code'],
                                                    'cobrand': self.cobrand})
        return mark_safe('''<a href="%s">%s</a>''' % (url, record['name']))

    class Meta:
        order_by = ('name',)

class BaseProblemTable(tables.Table):
    """
    Base class for functionality _all_ tables of problems need
    """

    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=("id"),
                                     attrs={'th': {'class': 'table__first'},
                                            'td': {'class': 'table__first'}})
    created = tables.DateTimeColumn(verbose_name="Received")
    status = tables.Column()
    category = tables.Column(verbose_name='Category')
    summary = tables.Column(verbose_name='Text snippet', order_by=("description"))

    def row_classes(self, record):
        if record.status in Problem.ESCALATION_STATUSES:
            return 'highlight'
        else:
            return ''

    def render_summary_as_response_link(self, record):
        response_link = reverse("response-form", kwargs={'pk': record.id})
        return mark_safe(u'<a href="{0}">{1}'.format(response_link, conditional_escape(record.private_summary)))

    def render_summary_as_public_link(self, record):
        # self.cobrand might not be set
        try:
            cobrand = self.cobrand or 'choices'
        except AttributeError:
            cobrand = 'choices'
        detail_link = reverse('problem-view', kwargs={'cobrand': cobrand, 'pk': record.id})
        return mark_safe('<a href="{0}">{1}'.format(detail_link, conditional_escape(record.summary)))


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

    def __init__(self, *args, **kwargs):
        self.private = kwargs.pop('private')
        if not self.private:
            self.cobrand = kwargs.pop('cobrand')
        super(ProblemTable, self).__init__(*args, **kwargs)

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

class QuestionsDashboardTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.", order_by=("id"))
    created = tables.DateTimeColumn(verbose_name="Received")
    summary = tables.Column(verbose_name='Text snippet', order_by=("description"))
    organisation = tables.Column(verbose_name="Organisation", default="None")
    action = tables.TemplateColumn(verbose_name='Actions',
                                    template_name='organisations/includes/question_link_column.html',
                                    orderable=False)

    class Meta:
        order_by = ('-created',)

class ProblemDashboardTable(BaseProblemTable):
    """
    A base Table class for all the different dashboards which show
    lists of problems. Quite similar to ProblemTable and ExtendedProblemTable
    but geared towards acting on problems, so not including satisfaction stats etc
    and always assuming a private context
    """

    breach = tables.TemplateColumn(template_name="organisations/includes/breach_column.html")

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        self.private = True
        super(ProblemDashboardTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'created',
                    'status',
                    'category',
                    'breach',
                    'summary')

class EscalationDashboardTable(ProblemDashboardTable):
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name',
                                  attrs={'th': {'class': 'table__first'},
                                         'td': {'class': 'table__first'}})
    # Redefine this to tell it that it's not table__first anymore
    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=("id"),
                                     attrs={'th': {'class': ''},
                                            'td': {'class': ''}})

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('provider_name',
                    'reference_number',
                    'created',
                    'status',
                    'category',
                    'breach',
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
    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=("id"),
                                     attrs={'th': {'class': ''},
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
