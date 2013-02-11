from django import forms

from citizenconnect.forms import MessageModelForm
from .models import Question

class QuestionForm(MessageModelForm):

    class Meta(MessageModelForm.Meta):
        model = Question
