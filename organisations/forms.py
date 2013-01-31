# Standard imports

# Django imports
from django import forms
from django.conf import settings

# App imports
from .choices_api import ChoicesAPI

class OrganisationFinderForm(forms.Form):
    organisation_type = forms.ChoiceField(choices=[('gppractices', 'GP'), ('hospitals', 'Hospital')])
    location = forms.CharField(required=True)