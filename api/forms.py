from django import forms
from django.forms.widgets import HiddenInput

from organisations.models import Organisation, Service
from problems.models import Problem
from questions.models import Question

class APIMessageModelForm(forms.ModelForm):
    """
    ModelForm implementation that does the basics for MessageModel model forms
    when data is supplied via the api, taking an extra source field.
    """
    # Make organisation a char field so that we can supply ods_codes to it
    organisation = forms.CharField(required=True)
    # Likewise for services, except making it a separate field
    service_code = forms.CharField(required=False)
    # Make source required
    source = forms.CharField(required=True)

    # Pull out the organisation ods_code and turn it into a real organisation
    def clean_organisation(self):
        cleaned_data = self.cleaned_data

        if 'organisation' in cleaned_data and cleaned_data['organisation']:
            try:
                return Organisation.objects.get(ods_code=cleaned_data['organisation'])
            except Organisation.DoesNotExist:
                raise forms.ValidationError('Sorry, that organisation is not recognised.')

    def clean_service(self):
        # Force the service foreign key field to be ignored, because we only
        # want to accept services via the service_code field we've added
        return None

    def clean(self):
        # Run super class clean method
        cleaned_data = super(APIMessageModelForm, self).clean()

        # Pull out the service_code and turn it into a real service
        # This has to be done here rather than in clean_service becauase
        # in clean_service we wouldn't have the organisation too
        if 'organisation' in cleaned_data and cleaned_data['organisation']:
            if 'service_code' in cleaned_data and cleaned_data['service_code']:
                try:
                    service = Service.objects.get(service_code=cleaned_data['service_code'],
                                                  organisation=cleaned_data['organisation'])
                    cleaned_data['service'] = service
                except Service.DoesNotExist:
                    # Add an error for this field
                    # See: https://docs.djangoproject.com/en/dev/ref/forms/validation/
                    # for why we have to do this rather than raise ValidationError
                    self._errors['service_code'] = self.error_class('Sorry, that service is not recognised.')
                    del cleaned_data['service_code']

        return cleaned_data

    class Meta:
        fields = [
            'organisation',
            'service_code',
            'service',
            'description',
            'category',
            'reporter_name',
            'reporter_phone',
            'reporter_email',
            'preferred_contact_method',
            'public',
            'public_reporter_name',
            'source'
        ]

        widgets = {
            'service': HiddenInput,
            'organisation': HiddenInput
        }

class QuestionAPIForm(APIMessageModelForm):

    class Meta(APIMessageModelForm.Meta):
        model = Question

class ProblemAPIForm(APIMessageModelForm):

    class Meta(APIMessageModelForm.Meta):
        model = Problem