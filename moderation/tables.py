import django_tables2 as tables
from issues.models import ProblemQuerySet

from organisations.table_columns import BreachAndEscalationColumn


class BaseModerationTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=ProblemQuerySet.ORDER_BY_FIELDS_FOR_MODERATION_TABLE,
                                     attrs={'td': {'class': 'problem-table__heavy-text'}})

    created = tables.DateTimeColumn(verbose_name="Received")
    private_summary = tables.Column(verbose_name='Text snippet', orderable=False)

    images = tables.TemplateColumn(
        template_name="organisations/includes/tables/columns/images_column.html",
        accessor="images",
        orderable=False
    )

    class Meta:
        attrs = {'class': 'problem-table  problem-table--expanded'}
        order_by = 'reference_number'


class ModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                   template_name='moderation/includes/moderation_link.html',
                                   orderable=False)

    class Meta:
        attrs = {'class': 'problem-table  problem-table--expanded'}


class SecondTierModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                   template_name='moderation/includes/second_tier_moderation_link.html',
                                   orderable=False)
    breach_and_escalation = BreachAndEscalationColumn()

    class Meta:
        attrs = {'class': 'problem-table  problem-table--expanded'}
