from django import forms
from django.forms.widgets import HiddenInput, Textarea

from issues.models import Problem, Question

from .models import QuestionResponse, ProblemResponse

class MessageResponseForm(forms.ModelForm):
    """
    Base form class for creating/editing responses to Questions and Problems.
    """

    response = forms.CharField(required=False, widget=Textarea())

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
        fields = [
            'response',
            'message'
        ]

        widgets = {
            'message': HiddenInput
        }

class QuestionResponseForm(MessageResponseForm):

    # Add a status field which will actually change the message this is
    # connected to
    message_status = forms.ChoiceField(choices=Question.STATUS_CHOICES,
                                       required=False)

    class Meta(MessageResponseForm.Meta):
        model = QuestionResponse

class ProblemResponseForm(MessageResponseForm):

    message_status = forms.ChoiceField(choices=Problem.STATUS_CHOICES,
                                       required=False)

    class Meta(MessageResponseForm.Meta):
        model = ProblemResponse