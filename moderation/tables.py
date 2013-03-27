from django.core.urlresolvers import reverse
import django_tables2 as tables

class BaseModerationTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.", order_by=("id"))
    created = tables.DateTimeColumn(verbose_name="Received")
    private_summary = tables.Column(verbose_name='Text snippet', order_by=("description"))

    class Meta:
        order_by = ('-created',)

class ModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                    template_name='moderation/includes/moderation_link.html',
                                    orderable=False)

class LegalModerationTable(BaseModerationTable):
    action = tables.TemplateColumn(verbose_name='Actions',
                                    template_name='moderation/includes/legal_moderation_link.html',
                                    orderable=False)
