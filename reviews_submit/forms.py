from django import forms
from django.forms.widgets import HiddenInput

from .models import Review, Rating


class ReviewForm(forms.ModelForm):

    def __init__(self, questions=None, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.questions = questions

    class Meta:
        model = Review

        fields = [
            'organisation',
            'email',
            'display_name',
            'is_anonymous',
            'title',
            'comment',
            'month_year_of_visit'
        ]

        widgets = {
            'organisation': HiddenInput
        }


class RatingForm(forms.ModelForm):

    class Meta:
        model = Rating

        fields = [
            'question',
            'answer'
        ]

