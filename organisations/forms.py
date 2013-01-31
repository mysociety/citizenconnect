# Standard imports

# Django imports
from django import forms
from django.conf import settings

# App imports
from .choices_api import ChoicesAPI

class OrganisationFinderForm(forms.Form):
    provider_type = forms.ChoiceField(choices=[('GP','GP'), ('Hospital', 'Hospital')])
    location = forms.CharField(required=True)