import datetime

from django import forms
from django.forms.widgets import Select, HiddenInput
from django.conf import settings

from .models import Review, Rating
from .widgets import MonthYearWidget


class ReviewForm(forms.ModelForm):

    # A check to make sure that people have read the T's & C's
    agree_to_terms = forms.BooleanField(required=True,
                                        error_messages={'required': 'You must agree to the terms and conditions to use this service.'})
    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)

        self.fields['title'].widget.attrs.update(
            {'placeholder': 'Please enter the title of your review'})

        self.fields['comment'].widget.attrs.update(
            {'placeholder': 'Please enter the main text of your review'})

        self.fields['month_year_of_visit'].label = 'When did you visit?'

    def clean_month_year_of_visit(self):
        month_year_of_visit = self.cleaned_data['month_year_of_visit']
        if month_year_of_visit > datetime.date.today():
            raise forms.ValidationError("The month and year of visit can't be in the future")

        # Check that the review date is not too long ago. Compare the year and
        # month seperately as we can't be sure about the day as we don't capture
        # it.
        oldest_permittable = datetime.date.today() - datetime.timedelta(days=settings.NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS)
        if self._mm_yyyy_lt_compare_dates(month_year_of_visit, oldest_permittable):
            raise forms.ValidationError("The month and year of visit can't be more than two years ago")

        return month_year_of_visit

    @classmethod
    def _mm_yyyy_lt_compare_dates(cls, dt_a, dt_b ):
        """Return True if dt_a is earlier than dt_b ignoring the days"""

        # If year is lower then always less
        if dt_a.year < dt_b.year:
            return True

        # If year is same then compare the months
        if dt_a.year == dt_b.year and dt_a.month < dt_b.month:
            return True

        # Otherwise not less
        return False


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
        self.fields['answer'].empty_label = '-- please select one --'

    class Meta:
        model = Rating

        fields = [
            'question',
            'answer'
        ]

        widgets = {
            'question': HiddenInput,
            'answer': Select
        }


def ratings_forms_for_review(review, request, questions):

    rating_forms = []
    for prefix, q in enumerate(questions):
        prefix += 1  # want these 1 based
        instance = Rating(question=q, review=review)

        rating_forms.append(
            RatingForm(
                q,
                data=request.POST or None,
                prefix=prefix,
                instance=instance
            )
        )

    return rating_forms
