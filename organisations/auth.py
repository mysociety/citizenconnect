from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

"""
Helpers to do with authorisation of users
"""

# User groups, so that we can have nice names for the groups
# to use in access checking queries
PROVIDERS = 1
NHS_SUPERUSERS = 2
CASE_HANDLERS = 3
QUESTION_ANSWERERS = 4
CCG = 6
SECOND_TIER_MODERATORS = 7
CUSTOMER_CONTACT_CENTRE = 8

ALL_GROUPS = [PROVIDERS,
              NHS_SUPERUSERS,
              CASE_HANDLERS,
              QUESTION_ANSWERERS,
              CCG,
              SECOND_TIER_MODERATORS,
              CUSTOMER_CONTACT_CENTRE]

def user_is_superuser(user):
    """
    Like Django's is_superuser, but it knows about NHS Superusers too
    """
    return user.is_superuser or user_in_group(user, NHS_SUPERUSERS)

def user_in_groups(user, groups):
    """
    Helper for seeing if a user is in any of a list of user groups.
    """
    return user.groups.filter(pk__in=groups).exists()

def user_in_group(user, group):
    return user_in_groups(user, [group])

def check_organisation_access(organisation, user):
    if not organisation.can_be_accessed_by(user):
        raise PermissionDenied()

def check_question_access(user):
    if not user_is_superuser(user) and not user_in_group(user, QUESTION_ANSWERERS):
        raise PermissionDenied()

def check_problem_access(problem, user):
    if not problem.can_be_accessed_by(user):
        raise PermissionDenied()

def check_response_access(problem, user):
    """
    Can a user respond to a problem?
    For now, this is equivalent to being able to access the organisation.
    """
    check_organisation_access(problem.organisation, user)

def user_can_access_escalation_dashboard(user):
    return (user_is_superuser(user) or user_in_groups(user, [CCG, CUSTOMER_CONTACT_CENTRE]))

def create_unique_username(organisation):
    """
    Try to create a unique username for an organisation.
    """
    username = organisation.name[:250]
    username = username.replace(' ', '_')
    username = ''.join([char for char in username if is_valid_username_char(char)])
    username = username.lower()
    if not User.objects.all().filter(username=username).exists():
        return username
    else:
        increment = 1
        possible_username = "{0}_{1}".format(username, increment)
        while User.objects.all().filter(username=possible_username).exists():
            possible_username = "{0}_{1}".format(username, increment)
            increment += 1
        return possible_username

def is_valid_username_char(char):
    """
    Is a character allowed in usernames?
    Only letters and underscores are allowed
    """
    return char.isalpha() or char == '_'
