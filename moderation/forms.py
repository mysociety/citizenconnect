from django import forms
from django.forms.widgets import HiddenInput

from problems.models import Problem
from questions.models import Question

class LookupForm(forms.Form):
    reference_number = forms.CharField(required=True)
    model_type = forms.CharField(widget=HiddenInput(), required=False)
    model_id = forms.CharField(widget=HiddenInput(), required=False)

    def clean(self):
        if 'reference_number' in self.cleaned_data:
            prefix = self.cleaned_data['reference_number'][:1]
            id = self.cleaned_data['reference_number'][1:]
            model = None

            try:
                if prefix == Problem.PREFIX:
                    model = Problem.open_objects.get(pk=id)
                elif prefix == Question.PREFIX:
                    model = Question.open_objects.get(pk=id)
                else:
                    raise forms.ValidationError('Sorry, that reference number is not recognised')
            except (Problem.DoesNotExist, Question.DoesNotExist):
                raise forms.ValidationError('Sorry, there are no open problems or questions with that reference number')

            self.cleaned_data['model_type'] = model.issue_type.lower()
            self.cleaned_data['model_id'] = model.id

        return self.cleaned_data