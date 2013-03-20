from django.core.urlresolvers import reverse
import django_tables2 as tables

class ModerationTable(tables.Table):

    reference_number = tables.Column(verbose_name="Ref.", order_by=("id"))
    created = tables.DateTimeColumn(verbose_name="Received")
    private_summary = tables.Column(verbose_name='Text snippet', order_by=("description"))
    action = tables.TemplateColumn(verbose_name='Actions',
                                    template_name='moderation/includes/moderation-link.html',
                                    orderable=False)

    class Meta:
        order_by = ('-created',)