from django import forms
from django.forms.widgets import HiddenInput, RadioSelect

class MessageModelForm(forms.ModelForm):
    """
    ModelForm implementation that does the basics for MessageModel model forms
    """

    # States of privacy
    PRIVACY_PRIVATE = '0'
    PRIVACY_PRIVATE_NAME = '1'
    PRIVACY_PUBLIC = '2'

    # A more user-friendly field with which to present the privacy options
    privacy = forms.ChoiceField(
        choices=((PRIVACY_PRIVATE, "Keep all details private"),
               (PRIVACY_PRIVATE_NAME, "Publish problem and response but not my name"),
               (PRIVACY_PUBLIC, 'Publish problem and response with my name')),
        initial=0,
        widget=RadioSelect,
        required=True
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        # Set public and public_reporter_name based on what they chose in privacy
        # Default to everything hidden
        cleaned_data['public'] = False
        cleaned_data['public_reporter_name'] = False
        if cleaned_data['privacy'] == self.PRIVACY_PRIVATE_NAME:
            cleaned_data['public'] = True
        elif cleaned_data['privacy'] == self.PRIVACY_PUBLIC:
            cleaned_data['public'] = True
            cleaned_data['public_reporter_name'] = True

        # Check that one of phone or email is provided
        if not cleaned_data['reporter_phone'] and not cleaned_data['reporter_email']:
            raise forms.ValidationError('You must provide either a phone number or an email address')

        return cleaned_data

    class Meta:
        fields = [
            'organisation',
            'description',
            'category',
            'reporter_name',
            'reporter_phone',
            'reporter_email',
            'preferred_contact_method',
            'public',
            'public_reporter_name'
        ]

        widgets = {
            # Hide this because it comes from the url already
            'organisation': HiddenInput,
            # Hide the privacy booleans because they're not very user-friendly
            # so we set them from the radio options in privacy instead
            'public': HiddenInput,
            'public_reporter_name': HiddenInput,
            # Make preferred contact method a radio button instead of a select
            'preferred_contact_method': RadioSelect
        }
