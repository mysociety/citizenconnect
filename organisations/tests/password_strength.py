from django import forms
from django.test import TestCase

from passwords.fields import PasswordField as PasswordFieldOriginal

# create a test form to use to check the validation


# replace with something that actually works
class PasswordField(PasswordFieldOriginal):
    pass


class TestingForm(forms.Form):
    password = PasswordField()


class PasswordStrengthTests(TestCase):

    test_username = 'username'

    unacceptable_passwords = [
        '123456789',  # too short
        'snohj*&A3',  # too short
        'aB3$efghi',  # too short

        'ab3$efvadzrk',  # no upper case
        'aBc$efvadzrk',  # no numbers
        'aB3defvadzrk',  # no punctuation
        'AB3DEFVADZRK',  # no lower case

        'username1@Xl',  # contains username
        'uSErnAMe1@Xl',  # contains username (in mixed case)
        'u53rname1@Xl',  # contains username (with number subs)

        'aB3$e gVad9r',  # no spaces
        'aB3$e,gVad9r',  # no commas
    ]

    acceptable_passwords = [
        'fhNzyH&%WtVVad9rkzE7Am'
    ]

    def is_password_valid(self, password):
        form = TestingForm({"password": password})
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


# Test that missing dict causes warning to be printed.
