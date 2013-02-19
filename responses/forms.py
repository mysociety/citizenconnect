from django import forms
from django.forms.widgets import HiddenInput

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

    class Meta(MessageResponseForm.Meta):
        model = QuestionResponse

class ProblemResponseForm(MessageResponseForm):

    class Meta(MessageResponseForm.Meta):
        model = ProblemResponse