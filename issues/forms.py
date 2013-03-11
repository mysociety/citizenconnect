import re

from ukpostcodeutils import validation

from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

from .models import Question, Problem

class MessageModelForm(forms.ModelForm):
    """
    ModelForm implementation that does the basics for MessageModel model forms
    """

    # States of privacy
    PRIVACY_PRIVATE = '0'
    PRIVACY_PRIVATE_NAME = '1'
    PRIVACY_PUBLIC = '2'

    # A more user-friendly field with which to present the privacy options
    # Note that the text is not used in the current templates, so this is
    # just generic text to explain them.
    privacy = forms.ChoiceField(
       choices=((PRIVACY_PRIVATE, "Keep all details private"),
                (PRIVACY_PRIVATE_NAME, "Publish with response but not my name"),
                (PRIVACY_PUBLIC, 'Publish with response and my name')),
       initial=0,
       widget=RadioSelect,
       required=True
    )

    # A check to make sure that people have read the T's & C's
    agree_to_terms = forms.BooleanField(required=True,
                                        error_messages={'required': 'You must agree to the terms and conditions to use this service.'})

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

        return cleaned_data

class QuestionForm(MessageModelForm):

    def clean_postcode(self):
        # Check that the postcode is valid
        postcode = self.cleaned_data['postcode']
        if postcode and not postcode == '':
            postcode = re.sub('\s+', '', postcode.upper())
            if not validation.is_valid_postcode(postcode):
                raise forms.ValidationError('Sorry, that doesn\'t seem to be a valid postcode.')
        return postcode

    class Meta:
        model = Question

        fields = [
            'description',
            'postcode',
            'category',
            'reporter_name',
            'reporter_phone',
            'reporter_email',
            'preferred_contact_method',
            'public',
            'public_reporter_name'
        ]

        widgets = {
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your question in this box.'}),
            'postcode': TextInput(attrs={'class': 'text-input'}),
            'category': RadioSelect,
            'reporter_name': TextInput(attrs={'class': 'text-input'}),
            # Add placeholder for phone
            'reporter_phone': TextInput(attrs={'class': 'text-input'}),
            # Add placeholder for email
            'reporter_email': TextInput(attrs={'class': 'text-input'}),
            # Make preferred contact method a radio button instead of a select
            'preferred_contact_method': RadioSelect,
            # Hide the privacy booleans because they're not very user-friendly
            # so we set them from the radio options in privacy instead
            'public': HiddenInput,
            'public_reporter_name': HiddenInput,
        }

class ProblemForm(MessageModelForm):

    class Meta:
        model = Problem

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
            # Make service a radio select
            'service': RadioSelect,
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your problem in this box'}),
            'category': RadioSelect,
            'reporter_name': TextInput(attrs={'class': 'text-input'}),
            # Add placeholder for phone
            'reporter_phone': TextInput(attrs={'class': 'text-input'}),
            # Add placeholder for email
            'reporter_email': TextInput(attrs={'class': 'text-input'}),
            # Make preferred contact method a radio button instead of a select
            'preferred_contact_method': RadioSelect,
            # Hide the privacy booleans because they're not very user-friendly
            # so we set them from the radio options in privacy instead
            'public': HiddenInput,
            'public_reporter_name': HiddenInput,
        }