import datetime
import re

from dateutil import relativedelta

from django import forms
from django.forms.widgets import Select, HiddenInput
from django.utils.dates import MONTHS

from .models import Review, Rating

from citizenconnect.forms import HoneypotModelForm

RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


def coerce_to_date(value):
    """Helper function to coerce a datestring into a date"""
    if isinstance(value, basestring):
        match = RE_DATE.match(value)
        if match:
            year_val, month_val, day_val = [int(v) for v in match.groups()]
            return datetime.date(year_val, month_val, day_val)


class ReviewForm(HoneypotModelForm):

    # A check to make sure that people have read the T's & C's
    agree_to_terms = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must agree to the terms and conditions to use this service.'}
    )

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)

        self.fields['title'].widget.attrs.update(
            {'placeholder': 'Please enter the title of your review'})

        self.fields['comment'].widget.attrs.update(
            {'placeholder': 'Please enter the main text of your review'})

        self.fields['month_year_of_visit'] = forms.TypedChoiceField(
            choices=self._month_choices(),
            coerce=coerce_to_date,
            required=True
        )
        self.fields['month_year_of_visit'].label = 'When did you visit?'

    @classmethod
    def _month_choices(cls):
        """Return a tuple of choices for the month_year_of_visit field."""
        # First, work out the range of months we want to show
        this_year = datetime.date.today().year
        this_month = datetime.date.today().month
        first_of_month = datetime.date(this_year, this_month, 1)
        twenty_four_months_ago = first_of_month - relativedelta.relativedelta(years=2)

        # Now make them into choices
        choices = []
        for year in range(twenty_four_months_ago.year, this_year + 1):
            for month in MONTHS:
                if year == twenty_four_months_ago.year and month < twenty_four_months_ago.month:
                    continue
                elif year == this_year and month > this_month:
                    continue

                choice_date = datetime.date(year, month, 1)
                choices.append((choice_date.strftime("%Y-%m-%d"), choice_date.strftime("%B %Y")))
        return tuple(choices)


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

    def __init__(self, question, *args, **kwargs):
        super(RatingForm, self).__init__(*args, **kwargs)

        self.question = question

        self.fields['question'].label = question.title

        self.fields['answer'].queryset = question.answers.all()
        self.fields['answer'].empty_label = '-- please select one --'

    def clean_answer(self):

        answer = self.cleaned_data.get('answer')

        if self.question.is_required and answer is None:
            raise forms.ValidationError("Rating is required.")

        return answer


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
    for q in questions:
        prefix = str(q.id)  # be sure that the form names are unique
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
