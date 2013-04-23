import django_tables2 as tables

class ReferenceNumberColumn(tables.TemplateColumn):

    def __init__(self, *args, **kwargs):

        kwargs['template_name'] = "issues/includes/reference_number_column.html"
        kwargs['verbose_name']  = "Ref."
        kwargs['order_by']      = ("id")

        return super(ReferenceNumberColumn, self).__init__(*args, **kwargs)
