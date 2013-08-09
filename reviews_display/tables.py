"""
Tables for displaying reviews.
"""

import django_tables2 as tables

from django.utils.text import Truncator
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string


class ReviewTable(tables.Table):

    """Table for organisation reviews pulled from the API."""

    api_posting_id = tables.Column(verbose_name='Ref',
                                   attrs={'th': {'class': 'one-twelfth'},
                                          'td': {'class': 'problem-table__heavy-text'}})
    api_published = tables.DateColumn(verbose_name='Received', format='d.m.Y',
                                      attrs={'th': {'class': 'two-twelfths  align-center'},
                                             'td': {'class': 'problem-table__light-text  align-center'}})

    rating = tables.Column(verbose_name='Rating',
                           accessor='ratings.all.0.score',
                           orderable=False,
                           attrs={'th': {'class': 'two-twelfths  align-center'}})

    content = tables.Column(verbose_name='Review',
                            orderable=False,
                            attrs={'th': {'class': 'seven-twelfths  align-center'}})

    def render_rating(self, record):
        return render_to_string('organisations/includes/rating_column.html', {'value': record.main_rating_score})

    def render_content(self, record, value):
        """Truncate the review's content to 20 words, returns a string."""
        truncated_content = Truncator(value).words(20)
        review_link = reverse('review-detail', kwargs={'ods_code': self.organisation.ods_code, 'cobrand': self.cobrand, 'api_posting_id': record.api_posting_id})
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right  fr" aria-hidden="true"></span></a>'.format(review_link, conditional_escape(truncated_content)))

    def row_classes(self, record):
        """Format rows as link classes, returns a string."""
        try:
            super_row_classes = super(ReviewTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    def row_href(self, record):
        return reverse(
            'review-detail',
            kwargs={
                'ods_code': self.organisation.ods_code,
                'cobrand': self.cobrand,
                'api_posting_id': record.api_posting_id
            }
        )

    def __init__(self, *args, **kwargs):
        """Overriden __init__ to take an extra organisation and cobrand parameters"""
        self.organisation = kwargs.pop('organisation', None)
        self.cobrand = kwargs.pop('cobrand', None)
        super(ReviewTable, self).__init__(*args, **kwargs)

    class Meta:
        order_by = ('-api_published',)
        attrs = {'class': 'problem-table problem-table--expanded'}


class OrganisationParentReviewTable(ReviewTable):

    """Table for the reviews for all the organisations under an Organisation Parent."""

    organisation_name = tables.Column(verbose_name='Provider name',
                                      accessor='organisations.all.0.name',
                                      attrs={'th': {'class': 'two-twelfths'}})

    def render_content(self, record, value):
        """Overriden render_content to use the first organisation from the
        record's organisations field instead of the table's organisation field"""
        truncated_content = Truncator(value).words(20)
        review_link = reverse('review-detail', kwargs={'ods_code': record.organisations.all()[0].ods_code, 'cobrand': 'choices', 'api_posting_id': record.api_posting_id})
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right  fr" aria-hidden="true"></span></a>'.format(review_link, conditional_escape(truncated_content)))

    def row_href(self, record):
        return reverse('review-detail', kwargs={'ods_code': record.organisations.all()[0].ods_code, 'cobrand': 'choices', 'api_posting_id': record.api_posting_id})

    class Meta:
        order_by = ('-api_published',)
        attrs = {'class': 'problem-table problem-table--expanded'}
        sequence = ('api_posting_id',
                    'organisation_name',
                    'api_published',
                    'rating',
                    'content')
