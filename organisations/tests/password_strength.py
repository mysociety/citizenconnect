from django.test import TestCase

from django.contrib.auth.models import User

from ..auth import StrongSetPasswordForm, StrongPasswordChangeForm


class PasswordStrengthTestsBase(object):

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

    def setUp(self):
        self.test_user = User(username='Billy')
        self.test_user.set_password('old_password')
        super(PasswordStrengthTestsBase, self).setUp()

    def is_password_valid(self, password):
        form = self.form_class(
            self.test_user,
            {
                "new_password1": password,
                "new_password2": password,
                "old_password": 'old_password',  # Needed for password change form validation
            }
        )
        if not form.is_valid():
            return False

        self.assertEqual(form.cleaned_data['new_password1'], password)

        return True

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


class StrongSetPasswordFormTests(PasswordStrengthTestsBase, TestCase):
    form_class = StrongSetPasswordForm


class StrongPasswordChangeFormTests(PasswordStrengthTestsBase, TestCase):
    form_class = StrongPasswordChangeForm
