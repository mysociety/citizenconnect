from django import forms

class MessageModerationForm(forms.ModelForm):
    """
    Base form class for moderating to Questions and Problems.

    Since these are just fields, this is basically another MessageModelForm,
    but with only the status field in it.
    """

    class Meta:
        fields = [
            'status'
        ]
