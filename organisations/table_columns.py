import django_tables2 as tables


class BreachColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        defaults = {
            'template_name': "organisations/includes/tables/columns/breach_column.html",
            'verbose_name': " ",
            'orderable': False,
            'attrs': {'td': {'class': 'problem-table__flag'}}
        }

        defaults.update(kwargs)

        return super(BreachColumn, self).__init__(*args, **defaults)
