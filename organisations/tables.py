import django_tables2 as tables

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from issues.tables import BaseProblemTable


class NationalSummaryTable(tables.Table):

    name = tables.Column(verbose_name='Provider name',
                         attrs={'th': {'class': 'two-twelfths'}})

    # We put all these columns in, and then js hides all but one
    week = tables.Column(verbose_name='Last 7 days',
                         attrs={'th': {'class': 'problems-received'}})
    four_weeks = tables.Column(verbose_name='Last 4 weeks',
                               attrs={'th': {'class': 'problems-received'}})
    six_months = tables.Column(verbose_name='Last 6 months',
                               attrs={'th': {'class': 'problems-received'}})
    all_time = tables.Column(verbose_name='All time',
                             attrs={'th': {'class': 'problems-received'}})

    # We split these into sub-columns
    average_time_to_acknowledge = tables.TemplateColumn(verbose_name='Acknowledge',
                                                        template_name='organisations/includes/tables/columns/time_interval_column.html')
    average_time_to_address = tables.TemplateColumn(verbose_name='Close',
                                                    template_name='organisations/includes/tables/columns/time_interval_column.html',
                                                    attrs={'th': {'class': 'summary-table__cell-no-border'}})

    # We split these into sub-columns
    happy_service = tables.TemplateColumn(verbose_name='Manner',
                                          template_name="organisations/includes/tables/columns/percent_column.html")

    happy_outcome = tables.TemplateColumn(verbose_name='Resolution',
                                          template_name="organisations/includes/tables/columns/percent_column.html",
                                          attrs={'th': {'class': 'summary-table__cell-no-border'}})

    # We put all these columns in, and then js hides all but one
    reviews_week = tables.Column(verbose_name='Last 7 days',
                                 attrs={'th': {'class': 'reviews-received'}})
    reviews_four_weeks = tables.Column(verbose_name='Last 4 weeks',
                                       attrs={'th': {'class': 'reviews-received'}})
    reviews_six_months = tables.Column(verbose_name='Last 6 months',
                                       attrs={'th': {'class': 'reviews-received'}})
    reviews_all_time = tables.Column(verbose_name='All time',
                                     attrs={'th': {'class': 'reviews-received'}})

    average_recommendation_rating = tables.TemplateColumn(verbose_name='Average Review:',
                                                          template_name='organisations/includes/tables/columns/rating_column.html',
                                                          attrs={'th': {'class': 'two-twelfths'}})

    def __init__(self, *args, **kwargs):
        self.cobrand = kwargs.pop('cobrand')
        super(NationalSummaryTable, self).__init__(*args, **kwargs)

    def render_name(self, record):
        url = self.reverse_to_org_summary(record['ods_code'])
        return mark_safe('''<a href="%s">%s</a>''' % (url, record['name']))

    def reverse_to_org_summary(self, ods_code):
        return reverse(
            'public-org-summary',
            kwargs={'ods_code': ods_code, 'cobrand': self.cobrand}
        )

    class Meta:
        # Show organisations with the most problems first. This is so that when
        # the results are filtered the top of the list (after it updates) is
        # more relevant. See issue #843 for rationale.
        order_by = ('-all_time',)


class CCGSummaryTable(NationalSummaryTable):

    def reverse_to_org_summary(self, ods_code):
        return reverse(
            'private-org-summary',
            kwargs={'ods_code': ods_code}
        )


class ProblemDashboardTable(BaseProblemTable):
    """
    A base Table class for all the different dashboards which show
    lists of problems. Quite similar to ProblemTable and ExtendedProblemTable
    but geared towards acting on problems, so not including satisfaction stats etc
    and always assuming a private context
    """
    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=('priority', 'created'),
                                     attrs={'td': {'class': 'problem-table__heavy-text'}})

    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name')

    service = tables.Column(verbose_name="Service", orderable=False)

    images = tables.TemplateColumn(
        template_name="organisations/includes/tables/columns/images_column.html",
        accessor="images",
        orderable=False
    )

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        kwargs['private'] = True
        super(ProblemDashboardTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('reference_number',)
        attrs = {'class': 'problem-table problem-table--expanded'}
        sequence = ('reference_number',
                    'provider_name',
                    'created',
                    'category',
                    'service',
                    'summary',
                    'images',
                    'breach')
