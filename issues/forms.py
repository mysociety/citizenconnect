import re

from ukpostcodeutils import validation

from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

from .models import Question, Problem
from .widgets import CategoryRadioFieldRenderer

class IssueModelForm(forms.ModelForm):
    """
    ModelForm implementation that does the basics for IssueModel model forms
    """

    # A check to make sure that people have read the T's & C's
    agree_to_terms = forms.BooleanField(required=True,
                                        error_messages={'required': 'You must agree to the terms and conditions to use this service.'})

class QuestionForm(IssueModelForm):

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
            'organisation',
            'description',
            'postcode',
            'reporter_name',
            'reporter_email',
        ]

        widgets = {
            'organisation': HiddenInput,
            # Add placeholder for description
            'description': Textarea({'placeholder': 'Please write the details of your question in this box.'}),
            'postcode': TextInput(attrs={'class': 'text-input'}),
            'reporter_name': TextInput(attrs={'class': 'text-input'}),
            # Add placeholder for email
            'reporter_email': TextInput(attrs={'class': 'text-input'}),
        }

class ProblemForm(IssueModelForm):

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

    # For some categories the reporter can elevate the priority of the report.
    # Javascript is used to disable this input if the category selected does not
    # permit this.
    elevate_priority = forms.BooleanField(
        required = False
    )

    # This is a honeypot field to catch spam bots. If there is any content in
    # it the form validation will fail and an appropriate error should be shown to
    # the user. This field is hidden by CSS in the form so should never be shown to
    # a user. Hopefully it will not be autofilled either.
    website = forms.CharField(
        label = 'Leave this blank',
        required = False,
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

        return super(ProblemForm, self).clean()


    def clean_website(self):
        # The field 'website' is a honeypot - it should be hidden from real
        # users. Anything that fills it in is probably a bot so reject the
        # submission.
        if self.cleaned_data.get('website'):
            raise forms.ValidationError("submission is probably spam")
        return ''


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
            'public_reporter_name',
            'relates_to_previous_problem',
        ]

        widgets = {
            # Hide this because it comes from the url already
            'organisation': HiddenInput,
            # Make service a radio select
            'service': RadioSelect,
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

class QuestionUpdateForm(forms.ModelForm):
    """
    Form for updating questions (by question-answerers)
    """

    class Meta:
        model = Question

        fields = [
            'response',
            'status'
        ]

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
            'happy_outcome',
        ]

        widgets = {
             'happy_outcome': RadioSelect(choices=SURVEY_CHOICES),
        }


class LookupForm(forms.Form):
    reference_number = forms.CharField(required=True)
    model_id = forms.CharField(widget=HiddenInput(), required=False)

    # TODO - this is a bit of hangover from when problems and questions
    # could be moderated, but now it's only problems
    def clean(self):
        if 'reference_number' in self.cleaned_data:
            prefix = self.cleaned_data['reference_number'][:1]
            id = self.cleaned_data['reference_number'][1:]
            try:
                if prefix.upper() == Problem.PREFIX:
                    problem = Problem.objects.all().get(pk=id)
                    self.cleaned_data['model_id'] = problem.id
                else:
                    raise forms.ValidationError('Sorry, that reference number is not recognised')
            except Problem.DoesNotExist:
                raise forms.ValidationError('Sorry, there are no problems with that reference number')
        return self.cleaned_data

