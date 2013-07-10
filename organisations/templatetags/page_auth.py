from django import template
register = template.Library()

from .. import auth
from ..auth import (user_is_escalation_body,
                    user_in_group,
                    user_in_groups,
                    user_is_superuser)


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


@register.filter()
def may_see_reporter_contact_details(user):
    """
    Returns true if the user may see the contact details of the reporter.
    """

    # currently limit to superusers until exact perms decided - see #873
    return user_is_superuser(user) or user_in_groups(user, [auth.CASE_HANDLERS, auth.ORGANISATION_PARENTS])
