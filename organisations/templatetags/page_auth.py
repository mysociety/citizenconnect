from django import template
register = template.Library()

from .. import auth
from ..auth import (user_can_access_escalation_dashboard,
                    user_can_access_private_national_summary,
                    user_is_escalation_body,
                    user_in_group)


@register.filter(is_safe=True)
def can_access(user, page):
    """
    Returns a boolean indicating whether the user can access the page named
    """
    if page == 'escalation-dashboard':
        return user_can_access_escalation_dashboard(user)
    if page == 'private-national-summary':
        return user_can_access_private_national_summary(user)
    return False


@register.filter(is_safe=True)
def is_ccg(user):
    """
    Returns a boolean indicating whether the user is a CCG
    """
    return user_in_group(user, auth.CCG)


@register.filter(is_safe=True)
def is_escalation_body(user):
    """
    Returns a boolean indicating whether the user is an escalation body

    EG: a CCG or the CCC, and hence needs some links to their escalation
    """
    return user_is_escalation_body(user)
