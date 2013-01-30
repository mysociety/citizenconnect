# Standard imports

# Django imports
from django import forms
from django.conf import settings

# App imports
from .choices_api import ChoicesAPI

class OrganisationFinderForm(forms.Form):
    choices_api = ChoicesAPI()
    organisations = choices_api.example_hospitals()
    organisation_list = [(org['id'], org['name']) for org in organisations]
    organisation = forms.ChoiceField(choices=organisation_list)
