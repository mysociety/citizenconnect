# Standard imports
import re
from ukpostcodeutils import validation

# Django imports
from django import forms
from django.conf import settings

# App imports
from citizenconnect.forms import MessageResponseForm
from problems.models import Problem
from questions.models import Question

import choices_api

class OrganisationFinderForm(forms.Form):
    organisation_type = forms.ChoiceField(choices=settings.ORGANISATION_CHOICES)
    location = forms.CharField(required=True, error_messages={'required': 'Please enter a location'})

    def clean(self):
        cleaned_data = super(OrganisationFinderForm, self).clean()
        location = cleaned_data.get('location', None)
        organisation_type = cleaned_data.get('organisation_type', None)
        if location and organisation_type:
            api = choices_api.ChoicesAPI()
            postcode = re.sub('\s+', '', location.upper())
            if validation.is_valid_postcode(postcode) or validation.is_valid_partial_postcode(postcode):
                search_type = 'postcode'
            else:
                search_type = 'name'
            organisations = api.find_organisations(organisation_type, search_type, location)
            if len(organisations) == 0:
                validation_message = "We couldn't find any matches for '%s'. Please try again." % (location)
                raise forms.ValidationError(validation_message)
            else:
                cleaned_data['organisations'] = organisations

        return cleaned_data

class QuestionResponseForm(MessageResponseForm):

    class Meta(MessageResponseForm.Meta):
        model = Question

class ProblemResponseForm(MessageResponseForm):

    class Meta(MessageResponseForm.Meta):
        model = Problem
