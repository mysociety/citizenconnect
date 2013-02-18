from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

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
            'service',
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
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your problem in this box, including as much information as possible to help us to help you'}),
            'category': RadioSelect,
            'reporter_name': TextInput(attrs={'placeholder': 'Your Name (This is optional - you can report problems anonymously)'}),
            # Add placeholder for phone
            'reporter_phone': TextInput(attrs={'placeholder': 'Your Contact Number (you must enter a contact number OR email address)'}),
            # Add placeholder for email
            'reporter_email': TextInput(attrs={'placeholder': 'Your Email Address (you must enter a contact number OR email address)'}),
            # Make preferred contact method a radio button instead of a select
            'preferred_contact_method': RadioSelect,
            # Hide the privacy booleans because they're not very user-friendly
            # so we set them from the radio options in privacy instead
            'public': HiddenInput,
            'public_reporter_name': HiddenInput,
        }

class MessageResponseForm(forms.ModelForm):
    """
    Base form class for creating/editing responses to Questions and Problems.

    Since these are just fields, this is basically another MessageModelForm,
    but with only the response field in it.
    """

    class Meta:
        fields = [
            'status',
            'response'
        ]

class MessageModerationForm(forms.ModelForm):
    """
    Base form class for moderating to Questions and Problems.

    Since these are just fields, this is basically another MessageModelForm,
    but with only the status field in it.
    """

    class Meta:
        fields = [
            'status'
        ]
