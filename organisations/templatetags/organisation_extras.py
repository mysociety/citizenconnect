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
