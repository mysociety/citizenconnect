from django import forms
from django.forms.widgets import HiddenInput, Textarea

from issues.models import Problem

from .models import ProblemResponse


class ProblemResponseForm(forms.ModelForm):

    response = forms.CharField(required=False, widget=Textarea())
    issue_status = forms.ChoiceField(choices=Problem.STATUS_CHOICES,
                                       required=False)

    def clean_response(self):
        response = self.cleaned_data['response']

        # If people clicked the "Respond" button, they must include a response
        if 'respond' in self.data and (not response or response == ''):
            raise forms.ValidationError('This field is required.')

        # If people clicked the "update status" button, and the added a response
        # we warn them that it won't get used
        if 'status' in self.data and response:
            raise forms.ValidationError('You cannot submit a response if you\'re just updating the status. Please delete the text in the response field or use the "Respond" button.')

        return response

    class Meta:
        model = ProblemResponse

        fields = [
            'response',
            'issue'
        ]

        widgets = {
            'issue': HiddenInput
        }
