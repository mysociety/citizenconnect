from django import forms
from django.forms.widgets import HiddenInput

from .models import Problem

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        widgets = {
            'organisation_type': HiddenInput,
            'choices_id': HiddenInput
        }