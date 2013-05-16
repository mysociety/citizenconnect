import django_tables2 as tables

from django.utils.text import Truncator


class ReviewTable(tables.Table):
    """
    Displays reviews that have been pulled back from the API for a given
    organisation.
    """

    api_posting_id = tables.Column(verbose_name='Ref',
                                   attrs={'td': {'class': 'problem-table__heavy-text'}})
    api_published = tables.DateColumn(verbose_name='Received Date',
                                  attrs={'td': {'class': 'problem-table__light-text'}})

    # TODO: There must be a better way to get the Friends and Family rating.
    # TODO: Change this to be a TemplateColumn once the ratings are merged.
    rating = tables.Column(verbose_name='Rating', accessor='ratings.all.0.score')

    content = tables.Column(verbose_name='Review', orderable=False)

    def render_content(self, value):
        return Truncator(value).words(20)

    def row_classes(self, record):
        try:
            super_row_classes = super(ReviewTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}
