from django import forms
from django.forms.widgets import HiddenInput, RadioSelect
from django.forms.models import inlineformset_factory

from issues.models import Problem
from responses.models import ProblemResponse

class LookupForm(forms.Form):
    reference_number = forms.CharField(required=True)
    model_id = forms.CharField(widget=HiddenInput(), required=False)

    # TODO - this is a bit of hangover from when problems and questions
    # could be moderated, but now it's only problems
    def clean(self):
        if 'reference_number' in self.cleaned_data:
            prefix = self.cleaned_data['reference_number'][:1]
            id = self.cleaned_data['reference_number'][1:]
            try:
                if prefix == Problem.PREFIX:
                    problem = Problem.objects.all().get(pk=id)
                    self.cleaned_data['model_id'] = problem.id
                else:
                    raise forms.ValidationError('Sorry, that reference number is not recognised')
            except Problem.DoesNotExist:
                raise forms.ValidationError('Sorry, there are no problems with that reference number')
        return self.cleaned_data

class ModerationForm(forms.ModelForm):

    def clean_publication_status(self):
        # Status is hidden, but if people click the "Publish" button, we should
        # publish it, and vice versa if they click "Keep Private", we default
        # to HIDDEN regardless for security
        publication_status = self.cleaned_data['publication_status']
        if 'publish' in self.data:
            publication_status = Problem.PUBLISHED
        else:
            publication_status = Problem.HIDDEN
        return publication_status

    def clean(self):

        # If we are publishing the problem and the reporter wants it public,
        # it must have a moderated_description so that we have something to show for it
        # on public pages
        if self.instance.public and self.cleaned_data['publication_status'] == Problem.PUBLISHED:
            if not 'moderated_description' in self.cleaned_data or not self.cleaned_data['moderated_description']:
                self._errors['moderated_description'] = self.error_class(['You must moderate a version of the problem details when publishing public problems.'])
                del self.cleaned_data['moderated_description']

        return self.cleaned_data



class ProblemModerationForm(ModerationForm):

    commissioned = forms.ChoiceField(widget=RadioSelect(), required=True, choices=Problem.COMMISSIONED_CHOICES)

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

    def clean_moderated(self):
        # If you are submitting the form, you have moderated it, so always return MODERATED
        return Problem.MODERATED

    class Meta:
        model = Problem

        fields = [
            'publication_status',
            'moderated_description',
            'moderated',
            'status',
            'requires_second_tier_moderation',
            'breach',
            'commissioned'
        ]

        widgets = {
            'publication_status': HiddenInput,
            'moderated': HiddenInput,
            'requires_second_tier_moderation': HiddenInput
        }

# A formset for the responses attached to a problem
ProblemResponseInlineFormSet = inlineformset_factory(Problem, ProblemResponse, max_num=0, fields=('response',))

class ProblemSecondTierModerationForm(ModerationForm):

    def clean_requires_second_tier_moderation(self):
        # If you are submitting the form, you have second tier moderated it, so always return False
        return False

    class Meta:
        model = Problem

        fields = [
            'publication_status',
            'moderated_description',
            'requires_second_tier_moderation'
        ]

        widgets = {
            'publication_status': HiddenInput,
            'requires_second_tier_moderation': HiddenInput
        }
