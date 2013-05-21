from django import forms
from django.forms.widgets import HiddenInput, Textarea

from citizenconnect.forms import ConcurrentFormMixin
from issues.models import Problem

from .models import ProblemResponse


class ProblemResponseForm(ConcurrentFormMixin, forms.ModelForm):

    response = forms.CharField(required=False, widget=Textarea())
    issue_status = forms.ChoiceField(choices=Problem.STATUS_CHOICES,
                                     required=False)
    issue_formal_complaint = forms.BooleanField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        super(ProblemResponseForm, self).__init__(request=request, *args, **kwargs)
        # Set the initial model
        self.concurrency_model = self.initial['issue']
        # If we're building a form for a GET request, set the initial session var
        if self.request.META['REQUEST_METHOD'] == 'GET':
            self.set_version_in_session()

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
        # Do a concurrency check
        if not self.concurrency_check():
            # Reset the issue version in the session
            self.set_version_in_session()
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
