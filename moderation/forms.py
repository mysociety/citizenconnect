from django import forms
from django.forms.widgets import HiddenInput

from issues.models import MessageModel, Problem, Question

class MessageModerationForm(forms.ModelForm):
    """
    Base form class for moderating to Questions and Problems.
    """

    def clean_publication_status(self):
        # Status is hidden, but if people click the "Publish" button, we should
        # publish it, and vice versa if they click "Keep Private"
        publication_status = self.cleaned_data['publication_status']
        if 'publish' in self.data:
            publication_status = MessageModel.PUBLISHED
        elif 'keep_private' in self.data:
            publication_status = MessageModel.HIDDEN
        return publication_status

    class Meta:
        fields = [
            'publication_status',
            'description',
        ]

        widgets = {
            'publication_status': HiddenInput
        }

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

class QuestionModerationForm(MessageModerationForm):

    class Meta(MessageModerationForm.Meta):
        model = Question

class ProblemModerationForm(MessageModerationForm):

    class Meta(MessageModerationForm.Meta):
        model = Problem
