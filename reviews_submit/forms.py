import datetime

from django import forms
from django.forms.widgets import RadioSelect, HiddenInput

from .models import Review, Rating
from .widgets import MonthYearWidget


class ReviewForm(forms.ModelForm):

    def clean_month_year_of_visit(self):
        month_year_of_visit = self.cleaned_data['month_year_of_visit']
        if month_year_of_visit > datetime.date.today():
            raise forms.ValidationError("The month and year of visit can't be in the future")
        return month_year_of_visit

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
            'organisation': HiddenInput,
            'month_year_of_visit': MonthYearWidget
        }


class RatingForm(forms.ModelForm):

    def __init__(self, question, *args, **kwargs):
        super(RatingForm, self).__init__(*args, **kwargs)
        self.fields['question'].label = question.title
        self.fields['answer'].queryset = question.answers.all()
        self.fields['answer'].empty_label = None

    class Meta:
        model = Rating

        fields = [
            'question',
            'answer'
        ]

        widgets = {
            'question': HiddenInput,
            'answer': RadioSelect
        }


def ratings_forms_for_review(review, request, questions):
    return [RatingForm(q, data=request.POST or None, prefix=q.id, instance=Rating(question=q, review=review)) for q in questions]