import re

from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.contrib.auth.forms import SetPasswordForm, PasswordChangeForm
from django.utils.translation import ugettext_lazy as _

from passwords.fields import PasswordField

"""
Helpers to do with authorisation of users
"""

# User groups, so that we can have nice names for the groups
# to use in access checking queries
PROVIDERS = 1
NHS_SUPERUSERS = 2
CASE_HANDLERS = 3
CCG = 6
SECOND_TIER_MODERATORS = 7
CUSTOMER_CONTACT_CENTRE = 8

ALL_GROUPS = [PROVIDERS,
              NHS_SUPERUSERS,
              CASE_HANDLERS,
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

def enforce_organisation_access_check(organisation, user):
    if not organisation.can_be_accessed_by(user):
        raise PermissionDenied()

def enforce_moderation_access_check(user):
    if not user_is_superuser(user) and not user_in_group(user, CASE_HANDLERS):
        raise PermissionDenied()

def enforce_second_tier_moderation_access_check(user):
    if not user_is_superuser(user) and not user_in_group(user, SECOND_TIER_MODERATORS):
        raise PermissionDenied()

def enforce_problem_access_check(problem, user):
    if not problem.can_be_accessed_by(user):
        raise PermissionDenied()

def enforce_response_access_check(problem, user):
    """
    Can a user respond to a problem?
    For now, this is equivalent to being able to access the organisation.
    """
    enforce_organisation_access_check(problem.organisation, user)

def user_can_access_escalation_dashboard(user):
    return (user_is_superuser(user) or user_in_groups(user, [CCG, CUSTOMER_CONTACT_CENTRE]))

def user_can_access_private_national_summary(user):
    if user_is_superuser(user) or user_in_group(user, CUSTOMER_CONTACT_CENTRE):
        return True

    # A CCG user with no CCGs should not be allowed.
    if user_in_group(user, CCG) and user.ccgs.count():
        return True

    return False


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





# note trying to create a form mixin that inherits from 'object' does not work
# - see http://stackoverflow.com/q/7114710 - instead we repeat a little bit of
# the code in each form class below


def validate_username_not_in_password(username, password):

    # Ignore case in this test
    username = username.lower()
    password = password.lower()

    if username in password:
        raise forms.ValidationError(
            "Password may not contain {0}".format(username))

    # list of characters that could be substituted for others
    substitutions = {
        '0': ['o'],
        '1': ['i', 'l'],
        '3': ['e'],
        '5': ['s'],
        '8': ['b'],
        '!': ['i', 'l'],
        '$': ['s'],
    }

    # generate the variations
    variations = [password]
    for from_char, to_array in substitutions.items():
        new_variations = []
        for variant in variations:
            for replacement in to_array:
                new_variant = re.sub(from_char, replacement, variant)
                new_variations.append(new_variant)
        variations = new_variations

    for variant in variations:
        if username in variant:
            raise forms.ValidationError(
                "Password may not contain {0} (even with some letters substituted".format(username))


def validate_password_allowed_chars(password):

    bad_chars = [' ', ',']

    for bad in bad_chars:
        if bad in password:
            raise forms.ValidationError(
                "Password may not contain '{0}'".format(bad))


class StrongSetPasswordForm(SetPasswordForm):

    new_password1 = PasswordField(label=_("New password"),
                                  widget=forms.PasswordInput)

    def clean_new_password1(self):
        if 'clean_new_password1' in dir(super(StrongSetPasswordForm, self)):
            super(StrongSetPasswordForm, self).clean_new_password1()
        validate_username_not_in_password(
            self.user.username, self.cleaned_data['new_password1'])
        validate_password_allowed_chars(self.cleaned_data['new_password1'])


class StrongPasswordChangeForm(PasswordChangeForm):

    new_password1 = PasswordField(label=_("New password"),
                                  widget=forms.PasswordInput)

    def clean_new_password1(self):
        if 'clean_new_password1' in dir(super(StrongPasswordChangeForm, self)):
            super(StrongPasswordChangeForm, self).clean_new_password1()
        validate_username_not_in_password(
            self.user.username, self.cleaned_data['new_password1'])
        validate_password_allowed_chars(self.cleaned_data['new_password1'])
