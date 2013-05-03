import re

from django import forms
from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm

from passwords.fields import PasswordField as PasswordFieldOriginal

# create a test form to use to check the validation


# replace with something that actually works
class PasswordField(PasswordFieldOriginal):
    pass


# note trying to create a form mixin that inherits from 'object' does not work
# - see http://stackoverflow.com/q/7114710 - instead testing that the code
# works when directly inheriting from the forms we want to override


def validate_username_not_in_password(username, password):

    # Ignore case in this test
    username = username.lower()
    password = password.lower()

    if username in password:
        raise forms.ValidationError("Password may not contain username")

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
                "Password may not contain username (even with some letters substituted")


def validate_password_allowed_chars(password):

    bad_chars = [' ', ',']

    for bad in bad_chars:
        if bad in password:
            raise forms.ValidationError("Password may not contain '{0}'".format(bad))


class StrongSetPasswordForm(SetPasswordForm):

    new_password1 = PasswordField()

    def clean_new_password1(self):
        if 'clean_new_password1' in dir(super(StrongSetPasswordForm, self)):
            super(StrongSetPasswordForm, self).clean_new_password1()
        validate_username_not_in_password(
            self.user.username, self.cleaned_data['new_password1'])
        validate_password_allowed_chars(self.cleaned_data['new_password1'])


class PasswordStrengthTests(TestCase):

    test_username = 'Billy'

    unacceptable_passwords = [
        '123456789',  # too short
        'snohj*&A3',  # too short
        'aB3$efghi',  # too short

        'ab3$efvadzrk',  # no upper case
        'aBc$efvadzrk',  # no numbers
        'aB3defvadzrk',  # no punctuation
        'AB3$EFVADZRK',  # no lower case

        'xxbillyx1@Xl',  # contains username
        'xxbILlyx1@Xl',  # contains username (in mixed case)
        'xx81L!yx1@Xl',  # contains username (with number subs)

        'aB3$ef adzrk',  # spaces not allowed
        'aB3$ef,adzrk',  # commas not allowed
    ]

    acceptable_passwords = [
        'fhNzyH&%WtVVad9rkzE7Am',   # proper random gibberish
        'EveryoneShould<3TheNHS!',  # concatenated words is ok
    ]

    def is_password_valid(self, password):
        form = StrongSetPasswordForm(
            User(username=self.test_username),
            {
                "new_password1": password,
                "new_password2": password,
            }
        )
        return form.is_valid()

    def test_unacceptable_passwords(self):
        for password in self.unacceptable_passwords:
            self.assertFalse(
                self.is_password_valid(password),
                "password '{0}' should not validate".format(password)
            )

    def test_acceptable_passwords(self):
        for password in self.acceptable_passwords:
            self.assertTrue(
                self.is_password_valid(password),
                "password '{0}' should validate".format(password)
            )
