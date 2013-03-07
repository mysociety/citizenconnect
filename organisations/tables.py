# encoding: utf-8

import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from issues.models import Problem

def percent():
    return """{% load organisation_extras %}{{value|percent}}"""

def formatted_time_interval():
    return """{% load organisation_extras %}{{value|formatted_time_interval}}"""

def boolean():
    return """{% load organisation_extras %}
              {% if value|formatted_boolean == 'True' %}
                <span class="icon-checkmark" aria-hidden="true"></span>
                <span class="hide-text">yes</span>
              {% elif value|formatted_boolean == 'False' %}
                <span class="icon-x" aria-hidden="true"></span>
                <span class="hide-text">no</span>
              {% else %}
                <span class="icon-circle" aria-hidden="true"></span>
                <span class="hide-text">—</span>
              {% endif %}"""

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
                                                template_code=formatted_time_interval())
    average_time_to_address = tables.TemplateColumn(verbose_name='Average time to address (days)',
                                            template_code=formatted_time_interval())
    happy_service = tables.TemplateColumn(verbose_name='% Happy with service',
                                          template_code=percent())
    happy_outcome = tables.TemplateColumn(verbose_name='% Happy with outcome',
                                          template_code=percent())

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
                                         template_code=boolean())
    happy_outcome = tables.TemplateColumn(verbose_name='Happy with outcome',
                                         template_code=boolean())
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
                                                template_code=formatted_time_interval())
    time_to_address = tables.TemplateColumn(verbose_name='Time to address (days)',
                                            template_code=formatted_time_interval())

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
