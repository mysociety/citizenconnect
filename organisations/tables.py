import django_tables2 as tables
from django_tables2.utils import A

class NationalSummaryTable(tables.Table):
    name = tables.LinkColumn('public-org-summary',
                             kwargs={'ods_code': A("ods_code"),
                                     'cobrand': A("cobrand")},
                             verbose_name='Provider name')
    week = tables.Column(verbose_name='Last 7 days')
    four_weeks = tables.Column(verbose_name='Last 4 weeks')
    six_months = tables.Column(verbose_name='Last 6 months')
    all_time = tables.Column(verbose_name='All time')
    percent_acknowledged = tables.Column(verbose_name='% Acknowledged in time')
    percent_addressed = tables.Column(verbose_name='% Addressed in time')
    percent_happy_service = tables.Column(verbose_name='% Happy with service')
    percent_happy_outcome = tables.Column(verbose_name='% Happy with outcome')

    class Meta:
        order_by = ('name',)
