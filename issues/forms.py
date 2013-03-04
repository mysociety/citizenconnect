from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

from .models import Question
from .models import Problem


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
       choices=(),
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

        return cleaned_data

class QuestionForm(MessageModelForm):

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.PRIVACY_CHOICES = ((self.PRIVACY_PRIVATE, "Keep all details private"),
                           (self.PRIVACY_PRIVATE_NAME, "Publish question and response but not my name"),
                           (self.PRIVACY_PUBLIC, 'Publish question and response with my name'))
        self.fields['privacy'].choices = self.PRIVACY_CHOICES

    class Meta:
        model = Question

        fields = [
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
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your question in this box, including as much information as possible to help us to help you'}),
            'category': RadioSelect,
            'reporter_name': TextInput(attrs={'placeholder': 'Your Name (This is optional - you can ask questions anonymously)'}),
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

class ProblemForm(MessageModelForm):

    def __init__(self, *args, **kwargs):
        super(ProblemForm, self).__init__(*args, **kwargs)
        self.PRIVACY_CHOICES = ((self.PRIVACY_PRIVATE, "Keep all details private"),
                                (self.PRIVACY_PRIVATE_NAME, "Publish problem and response but not my name"),
                                (self.PRIVACY_PUBLIC, 'Publish problem and response with my name'))
        self.fields['privacy'].choices = self.PRIVACY_CHOICES

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
