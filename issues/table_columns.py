import django_tables2 as tables


class ReferenceNumberColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        defaults = {
            'template_name': "issues/includes/reference_number_column.html",
            'verbose_name': "Ref.",
            'order_by': ("id"),
        }

        defaults.update(kwargs)

        return super(ReferenceNumberColumn, self).__init__(*args, **defaults)


class BreachAndEscalationColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        defaults = {
            'template_name': "issues/includes/breach_escalation_column.html",
            'verbose_name': " ",
            'orderable': False
        }

        defaults.update(kwargs)

        return super(BreachAndEscalationColumn, self).__init__(*args, **defaults)
