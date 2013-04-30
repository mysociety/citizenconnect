from django import forms
from django.forms.models import inlineformset_factory

from .models import Review, Rating


class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review

        fields = [
            'email',
            'display_name',
            'is_anonymous',
            'title',
            'comment',
            'month_year_of_visit'
        ]


class RatingForm(forms.ModelForm):

    class Meta:
        model = Rating


RatingFormSet = inlineformset_factory(Review, Rating, form=RatingForm, extra=7)
