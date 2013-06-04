# encoding: utf-8
from __future__ import division
from django import template
from django.forms import ChoiceField, TypedChoiceField, ModelChoiceField
from django.utils.encoding import force_unicode

register = template.Library()

@register.filter(is_safe=True)
def star_class(rating, current):
    """
    Should we fill in this star?
    """
    if rating >= current:
        return 'icon-star'
    elif rating >= (current - 0.5):
        return 'icon-star-2'
    else:
        return 'icon-star-3'

@register.filter(is_safe=True)
def percent(decimal):
    """
    Returns percentage formatted value for decimal
    """
    if decimal is None:
        return u'—'
    return "{0:.0f}%".format(decimal * 100)


@register.filter(is_safe=True)
def formatted_time_interval(time_in_minutes):
    """
    Returns a formatted time interval, given a decimal time in minutes
    """
    if time_in_minutes is None:
        return u'—'
    time_in_days = time_in_minutes/60/24
    time_in_days = "{0:.0f}".format(time_in_days)
    if time_in_days == '1':
        time_in_days = time_in_days + " day"
    else:
        time_in_days = time_in_days + " days"
    return time_in_days


@register.filter(is_safe=True)
def formatted_boolean(boolean):
    if boolean is True:
        return "True"
    elif boolean is False:
        return "False"
    else:
        return None


@register.filter(is_safe=True)
def row_classes(table, record):
    try:
        return table.row_classes(record)
    except AttributeError:
        return ""


@register.filter(is_safe=True)
def row_href(table, record):
    try:
        return table.row_href(record)
    except AttributeError:
        return ""


def paginator(context, adjacent_pages=2):
    """Base function for an ellipsis-capable paginator"""
    page_obj = context['page_obj']
    paginator = page_obj.paginator
    start_page = max(page_obj.number - adjacent_pages, 1)
    if start_page <= 3:
        start_page = 1
    end_page = page_obj.number + adjacent_pages + 1
    if end_page >= paginator.num_pages - 1:
        end_page = paginator.num_pages + 1
    page_numbers = [n for n in range(start_page, end_page)
                    if n > 0 and n <= paginator.num_pages]

    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'page_numbers': page_numbers,
        'show_first': 1 not in page_numbers,
        'show_last': paginator.num_pages not in page_numbers,
    }


def provider_paginator(context, adjacent_pages=2):
    """
    Adds pagination context variables for use in displaying first, adjacent and
    last page links in provider results

    Required context variables: page_obj: The Paginator.page() instance.
                                location: the provider location search
    """
    location = context['location']
    pagination_context = paginator(context, adjacent_pages)

    pagination_context['location'] = location
    return pagination_context


register.inclusion_tag('provider_paginator.html', takes_context=True)(provider_paginator)


def table_paginator(context, adjacent_pages=2):
    """
    Adds pagination context variables for use in displaying summary tables

    Required context variables: page_obj: The Paginator.page() instance.
                                table: the table
                                request: the request context
    """
    pagination_context = paginator(context, adjacent_pages)
    pagination_context['table'] = context['table']
    # Pass through the request context so that we can update querystrings with pagination params
    pagination_context['request'] = context['request']
    return pagination_context


register.inclusion_tag('organisations/includes/table_paginator.html', takes_context=True)(table_paginator)


@register.filter(name='display_value')
def display_value(field):
    """
    Returns the displayed value for this BoundField, as rendered in widgets.
    """
    value = field.value()
    if isinstance(field.field, ChoiceField) or \
       isinstance(field.field, TypedChoiceField) or \
       isinstance(field.field, ModelChoiceField):
        for (val, desc) in field.field.choices:
            # Have to do a string comparison because value will be a string
            # This is what the Select widget does too, honest:
            # https://github.com/django/django/blob/1.4.3/django/forms/widgets.py#L554-L555
            if force_unicode(val) == value:
                return desc
    return value
