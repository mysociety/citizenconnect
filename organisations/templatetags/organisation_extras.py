from __future__ import division
from django import template
register = template.Library()

@register.filter(is_safe=True)
def percent(decimal):
    """
    Returns percentage formatted value for decimal
    """
    if decimal == None:
        return '-'
    return "{0:.0f}%".format(decimal * 100)

