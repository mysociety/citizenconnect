# encoding: utf-8

from __future__ import division
from django import template
register = template.Library()

@register.filter(is_safe=True)
def percent(decimal):
    """
    Returns percentage formatted value for decimal
    """
    if decimal == None:
        return u'—'
    return "{0:.0f}%".format(decimal * 100)

@register.filter(is_safe=True)
def formatted_time_interval(time_in_minutes):
    """
    Returns a formatted time interval, given a decimal time in minutes
    """
    if time_in_minutes == None:
        return u'—'
    time_in_days = time_in_minutes/60/24
    time_in_days = "{0:.0f}".format(time_in_days)
    return time_in_days

@register.filter(is_safe=True)
def formatted_boolean(boolean):
    if boolean == True:
        return "True"
    elif boolean == False:
        return "False"
    else:
        return None

def paginator(context, adjacent_pages=2):
    """Base function for an ellipsis-capable paginator"""
    page_obj = context['page_obj']
    paginator = page_obj.paginator
    start_page = max(page_obj.number - adjacent_pages, 1)
    if start_page <= 3: start_page = 1
    end_page = page_obj.number + adjacent_pages + 1
    if end_page >= paginator.num_pages - 1: end_page = paginator.num_pages + 1
    page_numbers = [n for n in range(start_page, end_page) \
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
                                organisation_type: the provider type
    """
    location = context['location']
    organisation_type = context['organisation_type']
    pagination_context = paginator(context, adjacent_pages)

    pagination_context['location'] = location
    pagination_context['organisation_type'] = organisation_type
    return pagination_context

register.inclusion_tag('provider-paginator.html', takes_context=True)(provider_paginator)

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

register.inclusion_tag('organisations/includes/table-paginator.html', takes_context=True)(table_paginator)
