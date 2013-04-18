# Standard imports
import re
from ukpostcodeutils import validation
import json
import urllib
from itertools import chain

# Django imports
from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.db.models import Q

# App imports
from issues.models import Problem, Question

from .models import Organisation, CCG, Service
from .metaphone import dm

class OrganisationFinderForm(forms.Form):
    organisation_type = forms.ChoiceField(choices=settings.ORGANISATION_CHOICES, initial='hospitals')
    location = forms.CharField(required=True, error_messages={'required': 'Please enter a location'})

    def organisations_from_postcode(self, postcode, organisation_type, partial=False):
        path_elements = ['postcode']
        if partial:
            path_elements.append('partial')
        path_elements.append(urllib.quote(postcode))
        query_path = '/'.join(path_elements)
        url = "%(base_url)s%(query_path)s" % {'base_url': settings.MAPIT_BASE_URL,
                                              'query_path': query_path}
        try:
            point_response = urllib.urlopen(url)
        except IOError:
            validation_message = 'Sorry, our postcode lookup service is temporarily unavailable. Please try later or search by provider name'
            raise forms.ValidationError(validation_message)
        response_code = point_response.getcode()
        if response_code == 200:
            point_data = json.load(point_response)
            point = Point(point_data["wgs84_lon"], point_data["wgs84_lat"])
            return Organisation.objects.filter(point__distance_lt=(point, Distance(mi=5)),
                                               organisation_type=organisation_type).distance(point).order_by('distance')
        elif response_code == 404:
            validation_message = 'Sorry, no postcode matches that query. Please try again, or try searching by provider name'
            raise forms.ValidationError(validation_message)
        elif response_code == 400:
            validation_message = 'Sorry, that doesn\'t seem to be a valid postcode. Please try again, or try searching by provider name'
            raise forms.ValidationError(validation_message)
        else:
            validation_message = 'Sorry, our postcode lookup service is temporarily unavailable. Please try later or search by provider name'
            raise forms.ValidationError(validation_message)


    def clean(self):
        cleaned_data = super(OrganisationFinderForm, self).clean()
        location = cleaned_data.get('location', None)
        organisation_type = cleaned_data.get('organisation_type', None)
        if location and organisation_type:
            postcode = re.sub('\s+', '', location.upper())
            if validation.is_valid_postcode(postcode):
                organisations = self.organisations_from_postcode(postcode, organisation_type)
                validation_message = "Sorry, there are no matches within 5 miles of %s. Please try again." % (location)
            elif validation.is_valid_partial_postcode(postcode):
                organisations = self.organisations_from_postcode(postcode, organisation_type, partial=True)
                validation_message = "Sorry, there are no matches within 5 miles of %s. Please try again." % (location)
            else:
                organisations = Organisation.objects.filter(name__icontains=location,
                                                            organisation_type=organisation_type)
                if len(organisations) < 5 :
                    # Try a metaphone search to give more results
                    location_metaphone = dm(location)
                    # First do a __startswith or __endswith
                    alt_orgs = Organisation.objects.filter(Q(name_metaphone__startswith=location_metaphone[0])
                                                           | Q(name_metaphone__endswith=location_metaphone[0]),
                                                           Q(organisation_type=organisation_type),
                                                           ~Q(pk__in=list([a.id for a in organisations])))
                    organisations = list(chain(organisations, alt_orgs))
                    if len(organisations) < 10:
                        # Try a metaphone __contains to give even more results
                        more_orgs = Organisation.objects.filter(Q(name_metaphone__contains=location_metaphone[0]),
                                                                Q(organisation_type=organisation_type),
                                                                ~Q(pk__in=list([a.id for a in organisations])))
                        organisations = list(chain(organisations, more_orgs))

                validation_message = "We couldn't find any matches for '%s'. Please try again." % (location)
            if len(organisations) == 0:
                raise forms.ValidationError(validation_message)

            cleaned_data['organisations'] = organisations

        return cleaned_data

class FilterForm(forms.Form):
    """
    Form for processing filters on pages which filter issues
    """
    ccg = forms.ModelChoiceField(queryset=CCG.objects.all(), required=False, empty_label='CCG')
    organisation_type = forms.ChoiceField(choices=[('', 'Organisation type')] + settings.ORGANISATION_CHOICES,
                                          required=False)
    service_code = forms.ChoiceField(choices=[],required=False) # Choices set in __init__
    category = forms.ChoiceField(choices=[('', 'Problem category')] + list(Problem.CATEGORY_CHOICES),
                                 required=False)
    problem_statuses = [ [str(status), desc] for (status, desc) in Problem.VISIBLE_STATUS_CHOICES ]
    status = forms.TypedChoiceField(choices=[('', 'Problem status')] + problem_statuses,
                                    required=False,
                                    coerce=int)
    breach = forms.TypedChoiceField(choices=[['', 'Breach problems?'],
                                             [True, 'Breaches'],
                                             [False, 'Non-Breaches']],
                                    required=False,
                                    coerce=bool)

    def __init__(self, private=False, with_ccg=True, with_organisation_type=True,
                 with_service_code=True, with_category=True, with_status=True,
                 with_breach=True, *args, **kwargs):

        super(FilterForm, self).__init__(*args, **kwargs)

        # Turn off fields selectively
        if not with_ccg:
            del self.fields['ccg']

        if not with_organisation_type:
            del self.fields['organisation_type']

        if not with_service_code:
            del self.fields['service_code']
        else:
            # Do this at runtime, otherwise we can't test this form
            self.fields['service_code'].choices = [('', 'Department')] + list(Service.service_codes())

        if not with_category:
            del self.fields['category']

        if not with_status:
            del self.fields['status']
        else:
            if private:
                # Set status choices to all choices if we're on a private page
                # rather than the default of just public statuses
                all_statuses = [ [str(status), desc] for (status, desc) in Problem.STATUS_CHOICES ]
                self.fields['status'].choices = [('', 'Problem status')] + all_statuses

        if not with_breach:
            del self.fields['breach']

