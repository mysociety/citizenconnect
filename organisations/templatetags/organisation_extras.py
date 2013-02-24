from __future__ import division
from django import template
register = template.Library()

@register.filter(is_safe=True)
def true_to_false_percent(attributes, field_name):
    """
    Returns percentage of true to false counts for the given attribute
    """
    true_count = attributes["%s_true" % field_name]
    false_count = attributes["%s_false" % field_name]
    total = true_count+false_count
    if total == 0:
        return '-'
    return "{0:.0f}%".format(true_count/total * 100)

