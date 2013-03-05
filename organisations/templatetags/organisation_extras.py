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


def paginator(context, adjacent_pages=2):
    """
    Adds pagination context variables for use in displaying first, adjacent and
    last page links in provider results

    Required context variables: page_obj: The Paginator.page() instance.
                                location: the provider location search
                                organisation_type: the provider type
    """
    page_obj = context['page_obj']
    location = context['location']
    organisation_type = context.get('organisation_type')
    paginator = page_obj.paginator
    start_page = max(page_obj.number - adjacent_pages, 1)
    if start_page <= 3: start_page = 1
    end_page = page_obj.number + adjacent_pages + 1
    if end_page >= paginator.num_pages - 1: end_page = paginator.num_pages + 1
    page_numbers = [n for n in range(start_page, end_page) \
            if n > 0 and n <= paginator.num_pages]

    return {
        'location': location,
        'organisation_type': organisation_type,
        'page_obj': page_obj,
        'paginator': paginator,
        'page_numbers': page_numbers,
        'show_first': 1 not in page_numbers,
        'show_last': paginator.num_pages not in page_numbers,
    }

register.inclusion_tag('paginator.html', takes_context=True)(paginator)
