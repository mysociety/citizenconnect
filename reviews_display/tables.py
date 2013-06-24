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
        review_link = reverse('review-detail', kwargs={'ods_code': record.organisation.ods_code, 'cobrand': 'choices', 'api_posting_id': record.api_posting_id})
        return mark_safe(u'<a href="{0}">{1} <span class="icon-chevron-right  fr" aria-hidden="true"></span></a>'.format(review_link, conditional_escape(truncated_content)))

    def row_classes(self, record):
        """Format rows as link classes, returns a string."""
        try:
            super_row_classes = super(ReviewTable, self).row_classes(record)
        except AttributeError:
            super_row_classes = ""
        return '{0} table-link__row'.format(super_row_classes)

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}


class OrganisationParentReviewTable(ReviewTable):

    """Table for the reviews for all the organisations in a Trust."""

    organisation_name = tables.Column(verbose_name='Provider name',
                                      accessor='organisation.name',
                                      attrs={'th': {'class': 'two-twelfths'}})

    class Meta:
        order_by = ('-created',)
        attrs = {'class': 'problem-table problem-table--expanded'}
        sequence = ('api_posting_id',
                    'organisation_name',
                    'api_published',
                    'rating',
                    'content')
