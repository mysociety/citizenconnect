from django import forms
from django.forms.widgets import HiddenInput, Textarea

from citizenconnect.forms import ConcurrentFormMixin
from issues.models import Problem

from .models import ProblemResponse


class ProblemResponseForm(ConcurrentFormMixin, forms.ModelForm):

    response = forms.CharField(required=False, widget=Textarea())
    issue_status = forms.ChoiceField(choices=Problem.NON_ESCALATION_STATUS_CHOICES,
                                     required=False)
    issue_formal_complaint = forms.BooleanField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        super(ProblemResponseForm, self).__init__(request=request, *args, **kwargs)
        # Set the initial model
        self.concurrency_model = self.initial['issue']
        # If we're building a form for a GET request, set the initial session var
        if self.request.META['REQUEST_METHOD'] == 'GET':
            self.set_version_in_session()

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
