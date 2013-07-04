from django import forms
from django.forms.widgets import HiddenInput
from django.conf import settings

from organisations.models import Organisation, Service
from issues.models import Problem


class ProblemAPIForm(forms.ModelForm):

    # Make organisation a char field so that we can supply ods_codes to it
    organisation = forms.CharField(required=True)
    # Likewise for services, except making it a separate field
    service_code = forms.CharField(required=False)
    # Make source required
    source = forms.CharField(required=True)
    # Make commissioned required
    commissioned = forms.ChoiceField(required=True, choices=Problem.COMMISSIONED_CHOICES)
    # Add an escalated flag with which we'll set the Problem status
    escalated = forms.BooleanField(required=False)

    status = forms.IntegerField(required=False)
    # Make priority optional (we will set a default)
    priority = forms.IntegerField(required=False)

    # Make publication_status optional (we will set a default)
    publication_status = forms.IntegerField(required=False)

    # Make preferred_contact_method optional (we will set a default)
    preferred_contact_method = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(ProblemAPIForm, self).__init__(*args, **kwargs)
        # Add fields for the images for the problem
        for i in range(0, settings.MAX_IMAGES_PER_PROBLEM):
            self.fields['images_' + str(i)] = forms.ImageField(required=False)

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

    def clean_status(self):
        # Always set status to Problem.New. Note that if escalated is set
        # we will modify this in clean
        return Problem.NEW

    def clean_priority(self):
        if not self.cleaned_data.get('priority'):
            self.cleaned_data['priority'] = Problem.PRIORITY_NORMAL
        return self.cleaned_data['priority']

    def clean_preferred_contact_method(self):
        if not self.cleaned_data.get('preferred_contact_method'):
            self.cleaned_data['preferred_contact_method'] = Problem.CONTACT_EMAIL
        return self.cleaned_data['preferred_contact_method']

    def clean(self):
        # Run super class clean method
        cleaned_data = super(ProblemAPIForm, self).clean()

        # Pull out the service_code and turn it into a real service
        # This has to be done here rather than in clean_service becauase
        # in clean_service we wouldn't have the organisation too
        if cleaned_data.get('organisation') and cleaned_data.get('service_code'):
            try:
                service = Service.objects.get(service_code=cleaned_data['service_code'],
                                              organisation=cleaned_data['organisation'])
                cleaned_data['service'] = service
            except Service.DoesNotExist:
                # Add an error for this field
                # See: https://docs.djangoproject.com/en/dev/ref/forms/validation/
                # for why we have to do this rather than raise ValidationError
                self._errors['service_code'] = self.error_class(['Sorry, that service is not recognised.'])
                del cleaned_data['service_code']

        # Always mark problems as published, unless they require moderation
        if cleaned_data.get('requires_second_tier_moderation') is True:
            cleaned_data['publication_status'] = Problem.NOT_MODERATED
        else:
            cleaned_data['publication_status'] = Problem.PUBLISHED

        # If we are publishing the problem and the reporter wants it public,
        # it must have a moderated_description so that we have something to show for it
        # on public pages
        if cleaned_data.get('public') is True and cleaned_data.get('publication_status') == Problem.PUBLISHED:
            if not 'moderated_description' in cleaned_data or not cleaned_data['moderated_description']:
                self._errors['moderated_description'] = self.error_class(['You must moderate a version of the problem details when publishing public problems.'])
                del cleaned_data['moderated_description']

        if cleaned_data.get('priority') == Problem.PRIORITY_HIGH and not cleaned_data.get('category') in Problem.CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION:
            self._errors['priority'] = self.error_class(['The problem is not in a category which permits setting of a high priority.'])
            del cleaned_data['priority']

        # Raise an error if escalation flag is set - we don't support this yet
        if cleaned_data.get('escalated') is True:
            self._errors['escalated'] = self.error_class(['Escalation is not currently enabled.'])
            del cleaned_data['escalated']

        return cleaned_data

    class Meta:
        model = Problem

        fields = [
            'organisation',
            'service_code',
            'service',
            'description',
            'moderated_description',
            'requires_second_tier_moderation',
            'category',
            'reporter_name',
            'reporter_phone',
            'reporter_email',
            'preferred_contact_method',
            'public',
            'public_reporter_name',
            'publication_status',
            'source',
            'breach',
            'commissioned',
            'priority',
            'status'
        ]

        widgets = {
            'service': HiddenInput,
            'publication_status': HiddenInput,
            'organisation': HiddenInput,
            'status': HiddenInput
        }
