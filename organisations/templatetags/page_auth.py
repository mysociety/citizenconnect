from django import template
register = template.Library()

from ..auth import user_can_access_escalation_dashboard

@register.filter(is_safe=True)
def can_access(user, page):
    """
    Returns a boolean indicating whether the user can access the page named
    """
    if page == 'escalation-dashboard':
        return user_can_access_escalation_dashboard(user)
    return False

