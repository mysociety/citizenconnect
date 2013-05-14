import re

from ukpostcodeutils import validation

from django import forms
from django.forms.widgets import HiddenInput, RadioSelect, Textarea, TextInput

from .models import Problem
from .widgets import CategoryRadioFieldRenderer


class ProblemForm(forms.ModelForm):

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


    def save(self, commit=True):
        """
        Handle the save ourselves so we can set the priority (which is not a
        field we expect back from the form.)
        """

        problem = super(ProblemForm, self).save(commit=False)

        if self.cleaned_data['priority']:
            problem.priority = self.cleaned_data['priority']

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

        return super(ProblemForm, self).clean()


    def clean_elevate_priority(self):
        # If true, and the category premits it, set priority to true, otherwise
        # use default.
        may_elevate = self.cleaned_data['category'] in Problem.CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION

        if may_elevate and self.cleaned_data.get('elevate_priority'):
            self.cleaned_data['priority'] = Problem.PRIORITY_HIGH
        else:
            # None means the priority will fall through to whatever is the
            # default in the model
            self.cleaned_data['priority'] = None


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

