from django import forms
from django.forms.widgets import HiddenInput, RadioSelect
from django.forms.models import inlineformset_factory

from citizenconnect.forms import ConcurrentFormMixin
from issues.models import Problem
from responses.models import ProblemResponse


class ModerationForm(ConcurrentFormMixin, forms.ModelForm):

    def __init__(self, request=None, *args, **kwargs):
        super(ModerationForm, self).__init__(request=request, *args, **kwargs)
        # Set the initial model
        self.concurrency_model = self.instance
        # If we're building a form for a GET request, set the initial session vars
        if self.request.META['REQUEST_METHOD'] == 'GET':
            self.set_version_in_session()

        # We don't require the moderated_description field if the problem is not public.
        # Remove it from the form.
        if not self.instance.public:
            del self.fields['moderated_description']

        # If the name was not originally public then we don't need the public_reporter_name
        if self.instance.public_reporter_name_original is False:
            del self.fields['public_reporter_name']

        if 'status' in self.fields:
            # For now, restrict the statuses allowable to non-escalation statuses
            self.fields["status"].choices = Problem.NON_ESCALATION_STATUS_CHOICES

    def clean_publication_status(self):

        publication_status = self.cleaned_data['publication_status']

        # Status is hidden, but if people click the "Publish" button, we should
        # publish it, and vice versa if they click "Refer" we mark it as
        # not-moderated. We default to REJECTED regardless for security.
        publication_status = Problem.REJECTED

        if 'publish' in self.data or 'keep_private' in self.data:
            publication_status = Problem.PUBLISHED
        elif 'now_requires_second_tier_moderation' in self.data:
            publication_status = Problem.NOT_MODERATED

        return publication_status

    def clean_public(self):
        # If we are "keeping it private", we have to update the problem status
        # to private if it wasn't before
        if 'keep_private' in self.data:
            return False
        else:
            # We shouldn't be changing the public field
            return self.instance.public

    def clean(self):
        cleaned_data = super(ModerationForm, self).clean()

        # Check that the user's version of the issue is still the latest
        if not self.concurrency_check():
            self.set_version_in_session()
            # Raise an error to tell the user
            raise forms.ValidationError('Sorry, someone else has modified the Problem during the time you were working on it. Please double-check your changes to make sure they\'re still necessary.')

        # If we are publishing the problem and the reporter wants it public,
        # it must have a moderated_description so that we have something to show for it
        # on public pages
        if cleaned_data['public'] and cleaned_data['publication_status'] == Problem.PUBLISHED:
            if not 'moderated_description' in cleaned_data or not cleaned_data['moderated_description']:
                self._errors['moderated_description'] = self.error_class(['You must moderate a version of the problem details when publishing public problems.'])
                del cleaned_data['moderated_description']

        return cleaned_data


class ProblemModerationForm(ModerationForm):

    commissioned = forms.ChoiceField(widget=RadioSelect(), required=True, choices=Problem.COMMISSIONED_CHOICES)
    elevate_priority = forms.BooleanField(required=False)

    def __init__(self, request=None, *args, **kwargs):
        super(ProblemModerationForm, self).__init__(request=request, *args, **kwargs)
        # Set initial elevate_priority from priority field
        if self.instance.priority == Problem.PRIORITY_HIGH:
            self.fields["elevate_priority"].initial = True
        else:
            self.fields["elevate_priority"].initial = False

    def clean_elevate_priority(self):
        # Unlike on the problem form, we always allow moderators to set
        # or unset this field
        if self.cleaned_data.get('elevate_priority'):
            self.cleaned_data['priority'] = Problem.PRIORITY_HIGH
        else:
            self.cleaned_data['priority'] = Problem.PRIORITY_NORMAL

    def clean_requires_second_tier_moderation(self):
        # requires_second_tier_moderation is hidden, but if people click the "Requires Second Tier Moderation"
        # button, we should set it to True. If they click either "Publish" or "Keep Private",
        # we set it to False.
        requires_second_tier_moderation = self.cleaned_data['requires_second_tier_moderation']
        if 'now_requires_second_tier_moderation' in self.data:
            requires_second_tier_moderation = True
        else:
            requires_second_tier_moderation = False
        return requires_second_tier_moderation

    class Meta:
        model = Problem

        fields = [
            'publication_status',
            'moderated_description',
            'status',
            'requires_second_tier_moderation',
            'breach',
            'commissioned',
            'public_reporter_name',
            'public',
            'priority'
        ]

        widgets = {
            'publication_status': HiddenInput,
            'requires_second_tier_moderation': HiddenInput,
            'public': HiddenInput,
            'priority': HiddenInput
        }


ProblemResponseInlineFormSet = inlineformset_factory(Problem,
                                                     ProblemResponse,
                                                     max_num=0,
                                                     fields=('response',))


class ProblemSecondTierModerationForm(ModerationForm):

    public = forms.HiddenInput()

    def clean_requires_second_tier_moderation(self):
        # If you are submitting the form, you have second tier moderated it, so always return False
        return False

    class Meta:
        model = Problem

        fields = [
            'publication_status',
            'moderated_description',
            'requires_second_tier_moderation',
            'public_reporter_name',
            'public',
        ]

        widgets = {
            'publication_status': HiddenInput,
            'requires_second_tier_moderation': HiddenInput,
            'public': HiddenInput
        }
