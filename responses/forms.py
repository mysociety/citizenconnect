from django import forms
from django.forms.widgets import HiddenInput

from problems.models import Problem
from questions.models import Question

from .models import QuestionResponse, ProblemResponse

class MessageResponseForm(forms.ModelForm):
    """
    Base form class for creating/editing responses to Questions and Problems.
    """

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