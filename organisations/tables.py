# encoding: utf-8

import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
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

class MessageModelTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.", order_by=("id"))
    created = tables.DateTimeColumn(verbose_name="Received")
    status = tables.Column()
    category = tables.Column(verbose_name='Category')
    happy_service = tables.TemplateColumn(verbose_name='Happy with service',
                                         template_name="organisations/includes/boolean_column.html")
    happy_outcome = tables.TemplateColumn(verbose_name='Happy with outcome',
                                         template_name="organisations/includes/boolean_column.html")
    summary = tables.Column(verbose_name='Text snippet', order_by=("description"))

    def __init__(self, *args, **kwargs):

        self.private = kwargs.pop('private')
        self.message_type = kwargs.pop('message_type')
        if not self.private:
            self.cobrand = kwargs.pop('cobrand')
        super(MessageModelTable, self).__init__(*args, **kwargs)


    def render_summary(self, record):
        if self.private:
            url = reverse("response-form", kwargs={'message_type': self.message_type, 'pk': record.id})
        else:
            url = reverse('%s-view' % self.message_type, kwargs={'cobrand': self.cobrand, 'pk': record.id})
        return mark_safe('''<a href="%s">%s</a>''' % (url, record.summary))

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}



class ExtendedMessageModelTable(MessageModelTable):

    service = tables.Column(verbose_name='Department')
    time_to_acknowledge = tables.TemplateColumn(verbose_name='Time to acknowledge (days)',
                                                template_name='organisations/includes/time_interval_column.html')
    time_to_address = tables.TemplateColumn(verbose_name='Time to address (days)',
                                            template_name='organisations/includes/time_interval_column.html')

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'created',
                    'status',
                    'category',
                    'service',
                    'time_to_acknowledge',
                    'time_to_address',
                    'happy_service',
                    'happy_outcome',
                    'summary')
