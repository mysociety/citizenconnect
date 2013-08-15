import django_tables2 as tables


class BreachAndEscalationColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        defaults = {
            'template_name': "organisations/includes/tables/columns/breach_escalation_column.html",
            'verbose_name': " ",
            'orderable': False,
            'attrs': {'td': {'class': 'problem-table__flag'}}
        }

        defaults.update(kwargs)

        return super(BreachAndEscalationColumn, self).__init__(*args, **defaults)
