from django import forms
from django.forms.widgets import HiddenInput

from issues.models import Problem

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
                    problem = Problem.objects.unmoderated_problems().get(pk=id)
                    self.cleaned_data['model_id'] = problem.id
                else:
                    raise forms.ValidationError('Sorry, that reference number is not recognised')
            except Problem.DoesNotExist:
                raise forms.ValidationError('Sorry, there are no unmoderated problems with that reference number')
        return self.cleaned_data

class ProblemModerationForm(forms.ModelForm):

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

    def clean_moderated(self):
        # If you are submitting the form, you have moderated it, so always return MODERATED
        return Problem.MODERATED

    class Meta:
        model = Problem

        fields = [
            'publication_status',
            'description',
            'moderated'
        ]

        widgets = {
            'publication_status': HiddenInput,
            'moderated': HiddenInput
        }
