import django_tables2 as tables
from django_tables2.utils import A

from issues.models import Problem

class SummaryTable(tables.Table):
    sep_atts = {"th": {"class": "separator"},
                "td": {"class": "separator"}}

class NationalSummaryTable(SummaryTable):


    name = tables.LinkColumn('public-org-summary',
                             kwargs={'ods_code': A("ods_code"),
                                     'cobrand': A("cobrand")},
                             verbose_name='Provider name',
                             attrs=SummaryTable.sep_atts)
    week = tables.Column(verbose_name='Last 7 days')
    four_weeks = tables.Column(verbose_name='Last 4 weeks')
    six_months = tables.Column(verbose_name='Last 6 months')
    all_time = tables.Column(verbose_name='All time', attrs=SummaryTable.sep_atts)
    percent_acknowledged = tables.Column(verbose_name='% Acknowledged in time')
    percent_addressed = tables.Column(verbose_name='% Addressed in time', attrs=SummaryTable.sep_atts)
    percent_happy_service = tables.Column(verbose_name='% Happy with service')
    percent_happy_outcome = tables.Column(verbose_name='% Happy with outcome')

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

