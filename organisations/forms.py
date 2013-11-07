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
from issues.models import Problem
from citizenconnect.widgets import MonthYearWidget

from .models import Organisation, CCG, Service
from .metaphone import dm


class MapitError(Exception): pass
class MapitUnavailableError(MapitError): pass
class MapitPostcodeNotFoundError(MapitError): pass
class MapitPostcodeNotValidError(MapitError): pass


class MapitPostCodeLookup(object):

    @classmethod
    def postcode_to_point(cls, postcode, partial=False):

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
            raise MapitUnavailableError()

        response_code = point_response.getcode()
        if response_code == 200:
            point_data = json.load(point_response)
            point = Point(point_data["wgs84_lon"], point_data["wgs84_lat"])
            return point
        elif response_code == 404:
            raise MapitPostcodeNotFoundError()
        elif response_code == 400:
            raise MapitPostcodeNotValidError()
        else:
            raise MapitUnavailableError()



class OrganisationFinderForm(forms.Form):
    location = forms.CharField(required=True, error_messages={'required': 'Please enter a location'})

    PILOT_SEARCH_CAVEAT = 'The provider or postcode may not be covered by this service.'

    def organisations_from_postcode(self, postcode, partial=False):
        try:
            point = MapitPostCodeLookup.postcode_to_point(postcode, partial)
            return Organisation.objects.filter(point__distance_lt=(point, Distance(mi=5))).distance(point).order_by('distance')
        except MapitPostcodeNotFoundError:
            validation_message = 'Sorry, no postcode matches that query. Please try again, or try searching by provider name'
        except MapitPostcodeNotValidError:
            validation_message = 'Sorry, that doesn\'t seem to be a valid postcode. Please try again, or try searching by provider name'
        except MapitUnavailableError:
            validation_message = 'Sorry, our postcode lookup service is temporarily unavailable. Please try later or search by provider name'
        raise forms.ValidationError(validation_message)

    def clean(self):
        cleaned_data = super(OrganisationFinderForm, self).clean()
        location = cleaned_data.get('location', None)
        if location:
            postcode = re.sub('\s+', '', location.upper())
            if validation.is_valid_postcode(postcode):
                organisations = self.organisations_from_postcode(postcode)
                validation_message = "Sorry, there are no matches within 5 miles of %s. Please try again. %s" % (location, self.PILOT_SEARCH_CAVEAT)
            elif validation.is_valid_partial_postcode(postcode):
                organisations = self.organisations_from_postcode(postcode, partial=True)
                validation_message = "Sorry, there are no matches within 5 miles of %s. Please try again. %s" % (location, self.PILOT_SEARCH_CAVEAT)
            else:
                organisations = Organisation.objects.filter(name__icontains=location)
                if len(organisations) < 5:
                    # Try a metaphone search to give more results
                    location_metaphone = dm(location)
                    # First do a __startswith or __endswith
                    alt_orgs = Organisation.objects.filter(Q(name_metaphone__startswith=location_metaphone[0])
                                                           | Q(name_metaphone__endswith=location_metaphone[0]),
                                                           ~Q(pk__in=list([a.id for a in organisations])))
                    organisations = list(chain(organisations, alt_orgs))
                    if len(organisations) < 10:
                        # Try a metaphone __contains to give even more results
                        more_orgs = Organisation.objects.filter(Q(name_metaphone__contains=location_metaphone[0]),
                                                                ~Q(pk__in=list([a.id for a in organisations])))
                        organisations = list(chain(organisations, more_orgs))

                validation_message = "We couldn't find any matches for '%s'. Please try again. %s" % (location, self.PILOT_SEARCH_CAVEAT)
            if len(organisations) == 0:
                raise forms.ValidationError(validation_message)

            cleaned_data['organisations'] = organisations

        return cleaned_data


class FilterForm(forms.Form):
    """
    Form for processing filters on pages which filter issues
    """

    organisation = forms.ModelChoiceField(
        queryset=Organisation.objects.all(),
        required=False,
        empty_label='All',
        label="Organisation"
    )

    ccg = forms.ModelChoiceField(queryset=CCG.objects.all(), required=False, empty_label='All',
                                 label="CCG")

    organisation_type = forms.ChoiceField(choices=[('', 'All types')] + settings.ORGANISATION_CHOICES,
                                          required=False)

    # A service_code, eg: SRV123 which are consistent across the NHS
    # rather than the id of a specific service in our database, which refers
    # to an instance of service being provided at a specific organisation.
    service_code = forms.ChoiceField(choices=[], required=False, label="Service/Department")

    category = forms.ChoiceField(choices=[('', 'All categories')] + list(Problem.CATEGORY_CHOICES),
                                 required=False,
                                 label="Problem category")

    problem_statuses = [[str(status), desc] for (status, desc) in Problem.VISIBLE_STATUS_CHOICES]
    status = forms.TypedChoiceField(choices=[('', 'All statuses')] + problem_statuses,
                                    required=False,
                                    coerce=int,
                                    label="Problem status")

    flags = forms.TypedChoiceField(choices=[ ['', 'Choose severity'],
                                             ['breach', 'Breaches'],
                                             ['formal_complaint', 'Formal complaints'],
                                            ],
                                    required=False,
                                    empty_value=None,  # Default value is not coerced
                                  )

    def __init__(self, private=False, organisations=None, with_ccg=True, with_organisation_type=True,
                 with_service_code=True, with_category=True, with_status=True,
                 with_flags=True, *args, **kwargs):

        super(FilterForm, self).__init__(*args, **kwargs)

        # Turn off fields selectively
        if not organisations is None:
            self.fields['organisation'].queryset = organisations
        else:
            del self.fields['organisation']

        if not with_ccg:
            del self.fields['ccg']

        if not with_organisation_type:
            del self.fields['organisation_type']

        if not with_service_code:
            del self.fields['service_code']
        else:
            # We have to do this at runtime because otherwise we can't test this form
            self.fields['service_code'].choices = [('', 'All services/departments')] + list(Service.service_codes())

        if not with_category:
            del self.fields['category']

        if not with_status:
            del self.fields['status']
        else:
            if private:
                # Set status choices to all choices if we're on a private page
                # rather than the default of just public statuses
                all_statuses = [[str(status), desc] for (status, desc) in Problem.STATUS_CHOICES]
                self.fields['status'].choices = [('', 'Problem status')] + all_statuses

        if not private or (private and not with_flags):
            # flags are only for private pages (for now at least)
            del self.fields['flags']


class OrganisationFilterForm(FilterForm):
    """
    Subclass of FilterForm which filters problems when we're looking in the
    context of one specific organisation
    """

    def __init__(self, organisation, with_service_id=True, *args, **kwargs):
        """
        Overriden init to allow taking an organisation to extract services from
        """
        # Turn off things which don't make sense for one org
        kwargs['with_ccg'] = False
        kwargs['with_organisation_type'] = False
        kwargs['with_service_code'] = False
        super(OrganisationFilterForm, self).__init__(*args, **kwargs)

        if with_service_id:
            # Set the services from the organisation supplied
            # By inserting it here, we avoid having to re-order the fields
            services = organisation.services.all().order_by('name')
            self.fields.insert(0, 'service_id', forms.ModelChoiceField(queryset=services,
                                                                       required=False,
                                                                       empty_label="All services/departments",
                                                                       label="Service/Department"))


class SurveyAdminCSVUploadForm(forms.Form):
    """A Form for the admin site which allows bulk uploading of csv files"""
    csv_file = forms.FileField(
        label = 'CSV file',
    )

    location = forms.ChoiceField(
        choices=[['', 'Select a service']] + settings.SURVEY_LOCATION_CHOICES
    )

    context = forms.ChoiceField(choices=(('trust', 'Trust'), ('site', 'Site')))

    month = forms.DateField(widget=MonthYearWidget)


class SurveyLocationForm(forms.Form):
    """A Form for the survey page on organisations that lets you choose a
    location to show surveys for."""

    location = forms.ChoiceField(
        label="Select a service:",
        choices=settings.SURVEY_LOCATION_CHOICES,
        required=False
    )
