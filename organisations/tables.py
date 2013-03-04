import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from issues.models import Problem

def percent():
    return """{% load organisation_extras %}{{value|percent}}"""

class NationalSummaryTable(tables.Table):

    def __init__(self, *args, **kwargs):
        self.cobrand = kwargs.pop('cobrand')
        super(NationalSummaryTable, self).__init__(*args, **kwargs)


    sep_atts = {"th": {"class": "separator"},
                "td": {"class": "separator"}}
    name = tables.Column(verbose_name='Provider name',
                             attrs=sep_atts)
    week = tables.Column(verbose_name='Last 7 days')
    four_weeks = tables.Column(verbose_name='Last 4 weeks')
    six_months = tables.Column(verbose_name='Last 6 months')
    all_time = tables.Column(verbose_name='All time', attrs=sep_atts)
    average_time_to_acknowledge = tables.Column(verbose_name='Average time to acknowledge')
    average_time_to_address = tables.Column(verbose_name='Average time to address',
                                            attrs=sep_atts)
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
    happy_service = tables.BooleanColumn(verbose_name='Happy with service')
    happy_outcome = tables.BooleanColumn(verbose_name='Happy with outcome')
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


class ExtendedMessageModelTable(MessageModelTable):

    service = tables.Column(verbose_name='Department')
    time_to_acknowledge = tables.BooleanColumn(verbose_name='Time to acknowledge')
    time_to_address = tables.BooleanColumn(verbose_name='Time to address')

    class Meta:
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
