from django import forms
from django.forms.widgets import HiddenInput, Textarea

from issues.models import Problem

from .models import ProblemResponse


class ProblemResponseForm(forms.ModelForm):

    response = forms.CharField(required=False, widget=Textarea())
    message_status = forms.ChoiceField(choices=Problem.STATUS_CHOICES,
                                       required=False)

    def clean_response(self):
        response = self.cleaned_data['response']

        # If people clicked the "Respond" button, they must include a response
        if 'respond' in self.data and (not response or response == ''):
            raise forms.ValidationError('This field is required.')

        # If people clicked the "update status" button, we ignore the response
        if 'status' in self.data:
            response = None

        return response

    class Meta:
        model = ProblemResponse

        fields = [
            'response',
            'message'
        ]

        widgets = {
            'message': HiddenInput
        }
