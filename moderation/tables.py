from django.core.urlresolvers import reverse
import django_tables2 as tables
from issues.models import ProblemQuerySet

from issues.table_columns import ReferenceNumberColumn

class BaseModerationTable(tables.Table):

    reference_number = ReferenceNumberColumn(
        order_by=ProblemQuerySet.ORDER_BY_FIELDS_FOR_MODERATION_TABLE
    )

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
