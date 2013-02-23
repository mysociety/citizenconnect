import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from issues.models import Problem


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
    percent_acknowledged_in_time = tables.Column(verbose_name='% Acknowledged in time')
    percent_addressed_in_time = tables.Column(verbose_name='% Addressed in time', attrs=sep_atts)
    percent_happy_service = tables.Column(verbose_name='% Happy with service')
    percent_happy_outcome = tables.Column(verbose_name='% Happy with outcome')

    def render_name(self, record):
        url = reverse("public-org-summary", kwargs={'ods_code': record['ods_code'], 'cobrand': self.cobrand})
        return mark_safe('''<a href="%s">%s</a>''' % (url, record['name']))

    class Meta:
        order_by = ('name',)

class MessageModelTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.")
    created = tables.DateTimeColumn(verbose_name="Received")
    status = tables.Column()
    category = tables.Column(verbose_name='Category')
    happy_service = tables.BooleanColumn(verbose_name='Happy with service')
    happy_outcome = tables.BooleanColumn(verbose_name='Happy with outcome')
    summary = tables.Column(verbose_name='Text snippet')

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
    acknowledged_in_time = tables.BooleanColumn(verbose_name='Acknowledged in time')
    addressed_in_time = tables.BooleanColumn(verbose_name='Addressed in time')

    class Meta:
        sequence = ('reference_number',
                    'created',
                    'status',
                    'category',
                    'service',
                    'acknowledged_in_time',
                    'addressed_in_time',
                    'happy_service',
                    'happy_outcome',
                    'summary')
