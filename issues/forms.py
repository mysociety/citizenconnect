import re

from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

from .models import Problem
from .widgets import CategoryRadioFieldRenderer

from citizenconnect.forms import HoneypotModelForm


class ProblemForm(HoneypotModelForm):

    # A check to make sure that people have read the T's & C's
    agree_to_terms = forms.BooleanField(required=True,
                                        error_messages={'required': 'You must agree to the terms and conditions to use this service.'})

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
        initial=PRIVACY_PRIVATE,
        widget=RadioSelect,
        required=True
    )

    # For some categories the reporter can elevate the priority of the report.
    # Javascript is used to disable this input if the category selected does not
    # permit this.
    elevate_priority = forms.BooleanField(required=False)

    def save(self, commit=True):
        """
        Handle the save ourselves so we can set the priority (which is not a
        field we expect back from the form.)
        """

        problem = super(ProblemForm, self).save(commit=False)

        if self.cleaned_data['priority']:
            problem.priority = self.cleaned_data['priority']

        # Problems created using this should have a confirmation email sent,
        # if we have an email address.
        if problem.reporter_email:
            problem.confirmation_required = True

        if commit:
            problem.save()

        return problem

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

        # Override the public_reporter_name based on the reporter_under_16 setting
        if cleaned_data['reporter_under_16']:
            cleaned_data['public_reporter_name'] = False

        return super(ProblemForm, self).clean()

    def clean_elevate_priority(self):
        # If true, and the category premits it, set priority to true, otherwise
        # use default.
        may_elevate = self.cleaned_data.get('category') in Problem.CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION

        if may_elevate and self.cleaned_data.get('elevate_priority'):
            self.cleaned_data['priority'] = Problem.PRIORITY_HIGH
        else:
            # None means the priority will fall through to whatever is the
            # default in the model
            self.cleaned_data['priority'] = None

    def clean_reporter_phone(self):
        reporter_phone = self.cleaned_data.get('reporter_phone')
        if reporter_phone and re.search(r'[^\d\ \+]', reporter_phone):
            raise forms.ValidationError("Enter a valid phone number.")
        return reporter_phone

    def clean_preferred_contact_method(self):
        # Check that if they prefer to be contacted by phone, they actually provided a number
        reporter_phone = self.cleaned_data.get('reporter_phone')
        preferred_contact_method = self.cleaned_data.get('preferred_contact_method')

        # call this method, which will raise ValidationError if it fails
        Problem.validate_preferred_contact_method_and_reporter_phone(preferred_contact_method, reporter_phone)

        return preferred_contact_method

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
            'reporter_under_16',
            'preferred_contact_method',
            'public',
            'public_reporter_name',
        ]

        widgets = {
            # Hide this because it comes from the url already
            'organisation': HiddenInput,
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your problem in this box'}),
            'category': RadioSelect(renderer=CategoryRadioFieldRenderer),
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


class ProblemSurveyForm(forms.ModelForm):
    """Form for handling problem survey responses.
    """

    class Meta:
        model = Problem

        SURVEY_CHOICES = (
            ('', "I prefer not to answer"),
            (True, "Yes"),
            (False, "No")
        )

        fields = [
            'happy_service',
        ]

        widgets = {
            'happy_service': RadioSelect(choices=SURVEY_CHOICES),
        }


class LookupForm(forms.Form):
    reference_number = forms.CharField(required=True)
    model_id = forms.CharField(widget=HiddenInput(), required=False)

    def clean(self):
        if 'reference_number' in self.cleaned_data:
            prefix = self.cleaned_data['reference_number'][:1]

            try:
                id = int(self.cleaned_data['reference_number'][1:])
            except ValueError:
                raise forms.ValidationError('Sorry, that reference number is not recognised')

            try:
                if prefix.upper() == Problem.PREFIX:
                    problem = Problem.objects.all().get(pk=id)
                    self.cleaned_data['model_id'] = problem.id
                else:
                    raise forms.ValidationError('Sorry, that reference number is not recognised')
            except Problem.DoesNotExist:
                raise forms.ValidationError('Sorry, there are no problems with that reference number')
        return self.cleaned_data


class PublicLookupForm(LookupForm):

    def clean(self):
        """
        Overridden clean to allow a check on the problem's public visibility
        """
        cleaned_data = super(PublicLookupForm, self).clean()
        if 'reference_number' in self.cleaned_data:
            problem = Problem.objects.all().get(id=self.cleaned_data['model_id'])
            if problem.is_publicly_visible():
                return cleaned_data
            else:
                raise forms.ValidationError('Sorry, that reference number is not available')


class FeedbackForm(forms.Form):
    feedback_comments = forms.CharField(required=True, widget=forms.Textarea)
    name = forms.CharField(required=True, label="Your name")
    email = forms.EmailField(required=True,
                             help_text="Your email address won't be used as part of a mailing list or given to any third parties.")
