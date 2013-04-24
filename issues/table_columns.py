import django_tables2 as tables

class ReferenceNumberColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        defaults = {
            'template_name' : "issues/includes/reference_number_column.html",
            'verbose_name'  : "Ref.",
            'order_by'      : ("id"),
        }

        defaults.update(kwargs)

        return super(ReferenceNumberColumn, self).__init__(*args, **defaults)
