from django import forms

from problems.models import Problem
from questions.models import Question

class APIMessageModelForm(forms.ModelForm):
    """
    ModelForm implementation that does the basics for MessageModel model forms
    when data is supplied via the api, taking an extra source field.
    """

    class Meta:
        fields = [
            'organisation',
            'service',
            'description',
            'category',
            'reporter_name',
            'reporter_phone',
            'reporter_email',
            'preferred_contact_method',
            'public',
            'public_reporter_name',
            'source'
        ]

class QuestionAPIForm(APIMessageModelForm):

    class Meta(APIMessageModelForm.Meta):
        model = Question

class ProblemAPIForm(APIMessageModelForm):

    class Meta(APIMessageModelForm.Meta):
        model = Problem