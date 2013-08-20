import django_tables2 as tables

from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse

from .table_columns import BreachColumn


class BaseProblemTable(tables.Table):
    """
    Base class for functionality _all_ tables of problems need
    """

    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by='id',
                                     attrs={'td': {'class': 'problem-table__heavy-text'}})
    created = tables.DateTimeColumn(verbose_name="Received",
                                    attrs={'td': {'class': 'problem-table__light-text'}})
    category = tables.Column(verbose_name='Category', orderable=False)

    # The accessor might be changed to private_summary on private pages
    summary = tables.Column(verbose_name='Snippet',
                            orderable=False,
                            accessor="summary",
                            attrs={'td': {'class': 'problem-table__light-text'}})

    # Will only be made visible on private pages
    breach = BreachColumn(visible=False)

    def __init__(self, *args, **kwargs):
        self.private = kwargs.pop('private')
        if self.private:
            self.base_columns['summary'].accessor = 'private_summary'
            self.base_columns['breach'].visible = True
        else:
            self.cobrand = kwargs.pop('cobrand')
            self.base_columns['summary'].accessor = 'summary'
            self.base_columns['breach'].visible = False

        super(BaseProblemTable, self).__init__(*args, **kwargs)

    def render_summary_as_response_link(self, record):
        response_link = self.row_href(record)
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right" aria-hidden="true"></span></a>'.format(response_link, conditional_escape(record.private_summary)))

    def render_summary_as_public_link(self, record):
        detail_link = self.row_href(record)
        return mark_safe('<a href="{0}">{1}</a>'.format(detail_link, conditional_escape(record.summary)))

    def row_classes(self, record):
        try:
            super_row_classes = super(BaseProblemTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    def row_href(self, record):
        """Return an href for the given row

        Where we link to depends on whether this is public or private
        """

        if self.private:
            return reverse('response-form', kwargs={'pk': record.id})
        else:
            # self.cobrand might not be set
            try:
                cobrand = self.cobrand or 'choices'
            except AttributeError:
                cobrand = 'choices'
            return reverse('problem-view', kwargs={'pk': record.id, 'cobrand': cobrand})

    class Meta:
        attrs = {'class': 'problem-table problem-table--expanded'}


class ProblemTable(BaseProblemTable):
    """
    A table for an overview of public or private lists of problems related to a provider.
    Explicitly not for dashboards, where action related to those problems
    is implied or the primary focus.
    """
    happy_service = tables.TemplateColumn(verbose_name='Manner',
                                          template_name="organisations/includes/tables/columns/boolean_column.html",
                                          orderable=False)
    happy_outcome = tables.TemplateColumn(verbose_name='Resolution',
                                          template_name="organisations/includes/tables/columns/boolean_column.html",
                                          orderable=False)
    status = tables.Column()

    split_columns = True

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
                    'summary',
                    'breach')


class ExtendedProblemTable(ProblemTable):
    """
    Like ProblemTable but for organisations where has_services and
    has_time_limits are true meaning we show extra stats
    """
    service = tables.Column(verbose_name='Department', orderable=False)
    time_to_acknowledge = tables.TemplateColumn(verbose_name='Acknowledge',
                                                template_name='organisations/includes/tables/columns/time_interval_column.html',
                                                orderable=False)
    time_to_address = tables.TemplateColumn(verbose_name='Close',
                                            template_name='organisations/includes/tables/columns/time_interval_column.html',
                                            orderable=False)
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
                    'summary',
                    'breach')


class OrganisationParentProblemTable(ExtendedProblemTable):
    """
    Like ExtendedProblemTable but for Organisation Parents, so including a provider name column
    """
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name')

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'provider_name',
                    'created',
                    'status',
                    'resolved',
                    'category',
                    'service',
                    'time_to_acknowledge',
                    'time_to_address',
                    'happy_service',
                    'happy_outcome',
                    'summary',
                    'breach')


class BreachTable(ProblemTable):
    """
    Annoyingly quite like ProblemTable, but with provider_name in as well
    """
    provider_name = tables.Column(verbose_name='Provider name',
                                  accessor='organisation.name')

    def __init__(self, *args, **kwargs):
        # Private is always true for dashboards
        self.private = True
        super(BreachTable, self).__init__(*args, **kwargs)

    def render_summary(self, record):
        return self.render_summary_as_response_link(record)

    class Meta:
        order_by = ('-created',)
        attrs = {"class": "problem-table"}
        sequence = ('reference_number',
                    'provider_name',
                    'created',
                    'status',
                    'category',
                    'happy_service',
                    'happy_outcome',
                    'summary')
        split_columns = True
