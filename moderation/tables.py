import django_tables2 as tables
from issues.models import ProblemQuerySet


class BaseModerationTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.",
                                     order_by=ProblemQuerySet.ORDER_BY_FIELDS_FOR_MODERATION_TABLE,
                                     attrs={'td': {'class': 'problem-table__heavy-text'}})

    created = tables.DateTimeColumn(verbose_name="Received")
    private_summary = tables.Column(verbose_name='Text snippet', order_by=("description"))


class ModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                   template_name='moderation/includes/moderation_link.html',
                                   orderable=False)


class SecondTierModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                   template_name='moderation/includes/second_tier_moderation_link.html',
                                   orderable=False)
