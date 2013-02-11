from django import forms

from citizenconnect.forms import MessageModelForm
from .models import Problem

class ProblemForm(MessageModelForm):

    class Meta(MessageModelForm.Meta):
        model = Problem
