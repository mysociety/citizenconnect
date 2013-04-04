from django import forms
from django.forms.widgets import HiddenInput, Textarea

from issues.models import Problem

from .models import ProblemResponse


class ProblemResponseForm(forms.ModelForm):

    response = forms.CharField(required=False, widget=Textarea())
    issue_status = forms.ChoiceField(choices=Problem.STATUS_CHOICES,
                                     required=False)

    def __init__(self, request=None, *args, **kwargs):
        # Store the request so we can use it later
        self.request = request
        super(ProblemResponseForm, self).__init__(*args, **kwargs)

    def clean_response(self):
        response = self.cleaned_data['response']

        # If people clicked the "Respond" button, they must include a response
        if 'respond' in self.data and not response:
            raise forms.ValidationError('This field is required.')

        # If people clicked the "update status" button, and the added a response
        # we warn them that it won't get used
        if 'status' in self.data and response:
            raise forms.ValidationError('You cannot submit a response if you\'re just updating the status. Please delete the text in the response field or use the "Respond" button.')

        return response

    def clean(self):
        cleaned_data = super(ProblemResponseForm, self).clean()
        # Check that the user's version of the issue is still the latest
        issue = cleaned_data['issue']
        # session_version was set on the initial GET for the form view
        session_version = self.request.session.get('problem_versions')[issue.id]
        if session_version != issue.version:
            # Reset the issue version in the session
            self.request.session['problem_versions'][issue.id] = issue.version
            # We need to do this because we haven't modified request.session itself
            self.request.session.modified = True
            # Raise an error to tell the user
            raise forms.ValidationError('Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')
        return cleaned_data

    class Meta:
        model = ProblemResponse

        fields = [
            'response',
            'issue'
        ]

        widgets = {
            'issue': HiddenInput
        }
