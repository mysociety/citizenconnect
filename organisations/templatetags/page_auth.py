from django import template
register = template.Library()

from .. import auth
from ..auth import (user_is_escalation_body,
                    user_in_group)


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
