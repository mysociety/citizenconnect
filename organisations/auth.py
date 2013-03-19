from django.contrib.auth.models import User, Group

"""
Helpers to do with authorisation of users
"""

# User groups, so that we can have nice names for the groups
# to use in access checking queries
PROVIDERS = 1
NHS_SUPERUSERS = 2
CASE_HANDLERS = 3
QUESTION_ANSWERERS = 4
CQC = 5
CCG = 6

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
