import django_tables2 as tables
from django_tables2.utils import A

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from issues.models import Problem

class SummaryTable(tables.Table):
    sep_atts = {"th": {"class": "separator"},
                "td": {"class": "separator"}}

class NationalSummaryTable(SummaryTable):

    def __init__(self, *args, **kwargs):
        self.cobrand = kwargs.pop('cobrand')
        super(NationalSummaryTable, self).__init__(*args, **kwargs)

    name = tables.Column(verbose_name='Provider name',
                             attrs=SummaryTable.sep_atts)
    week = tables.Column(verbose_name='Last 7 days')
    four_weeks = tables.Column(verbose_name='Last 4 weeks')
    six_months = tables.Column(verbose_name='Last 6 months')
    all_time = tables.Column(verbose_name='All time', attrs=SummaryTable.sep_atts)
    percent_acknowledged = tables.Column(verbose_name='% Acknowledged in time')
    percent_addressed = tables.Column(verbose_name='% Addressed in time', attrs=SummaryTable.sep_atts)
    percent_happy_service = tables.Column(verbose_name='% Happy with service')
    percent_happy_outcome = tables.Column(verbose_name='% Happy with outcome')

    def render_name(self, record):
        url = reverse("public-org-summary", kwargs={'ods_code': record['ods_code'], 'cobrand': self.cobrand})
        return mark_safe('''<a href="%s">%s</a>''' % (url, record['name']))

    class Meta:
        order_by = ('name',)

class ProblemTable(SummaryTable):

    reference_number = tables.Column(verbose_name="Ref.")
    created = tables.Column(verbose_name="Received")
    status = tables.Column()
    category = tables.Column(verbose_name='Category')
    service = tables.Column(verbose_name='Department')
    happy_service = tables.Column(verbose_name='Happy with service')
    happy_outcome = tables.Column(verbose_name='Happy with outcome')
    summary = tables.Column(verbose_name='Text snippet')
    class Meta:
        order_by = ('-created')

