from django import template
register = template.Library()

from .. import auth
from ..auth import (user_in_group,
                    user_in_groups,
                    user_is_superuser)


@register.filter(is_safe=True)
def is_ccg(user):
    """
    Returns a boolean indicating whether the user is a CCG
    """
    return user_in_group(user, auth.CCG)


@register.filter()
def may_see_reporter_contact_details(user):
    """
    Returns true if the user may see the contact details of the reporter.
    """

    permitted_groups = [auth.CASE_HANDLERS, auth.ORGANISATION_PARENTS]
    return user_is_superuser(user) or user_in_groups(user, permitted_groups)
