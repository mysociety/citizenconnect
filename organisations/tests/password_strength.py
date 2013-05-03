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
    if username in password:
        raise forms.ValidationError("Password may not contain variation of username")


class StrongSetPasswordForm(SetPasswordForm):

    new_password1 = PasswordField()

    def clean_new_password1(self):
        if 'clean_new_password1' in dir(super(StrongSetPasswordForm, self)):
            super(StrongSetPasswordForm, self).clean_new_password1()
        validate_username_not_in_password(
            self.user.username, self.cleaned_data['new_password1'])


class PasswordStrengthTests(TestCase):

    test_username = 'username'

    unacceptable_passwords = [
        '123456789',  # too short
        'snohj*&A3',  # too short
        'aB3$efghi',  # too short

        'ab3$efvadzrk',  # no upper case
        'aBc$efvadzrk',  # no numbers
        'aB3defvadzrk',  # no punctuation
        'AB3$EFVADZRK',  # no lower case

        'username1@Xl',  # contains username
        # 'uSErnAMe1@Xl',  # contains username (in mixed case)
        # 'u53rname1@Xl',  # contains username (with number subs)

        # 'aB3$e gVad9r',  # spaces not allowed
        # 'aB3$e,gVad9r',  # commas not allowed
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
