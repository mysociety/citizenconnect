from django import template
register = template.Library()

from organisations.templatetags.organisation_extras import paginator

def live_feed_paginator(context, adjacent_pages=2):
    """
    Adds pagination context variables for use in displaying the live feed

    Required context variables: page_obj: The Paginator.page() instance.
                                request: the request context
    """
    pagination_context = paginator(context, adjacent_pages)
    # Pass through the request context so that we can update querystrings with pagination params
    pagination_context['request'] = context['request']
    return pagination_context


register.inclusion_tag('citizenconnect/includes/live_feed_paginator.html', takes_context=True)(live_feed_paginator)
