from itertools import chain
from operator import attrgetter

# Django imports
from django.views.generic import TemplateView

# App imports
from problems.models import Problem
from questions.models import Question

class ModerateHome(TemplateView):
    template_name = 'moderation/moderate-home.html'

    def get_context_data(self, **kwargs):
        # Get all the problems and questions
        context = super(ModerateHome, self).get_context_data(**kwargs)
        # Get all the open problems and questions
        problems = Problem.objects.open_problems().order_by("created")
        questions = Question.objects.open_questions().order_by("created")
        context['problems'] = problems
        context['questions'] = questions
        # Put them into one list, taken from http://stackoverflow.com/questions/431628/how-to-combine-2-or-more-querysets-in-a-django-view
        issues = sorted(
            chain(problems, questions),
            key=attrgetter('created'),
            reverse=True
        )
        context['issues'] = issues
        return context

class ModerateLookup(TemplateView):
    template_name = 'moderation/moderate-lookup.html'

class ModerateForm(TemplateView):
    template_name = 'moderation/moderate-form.html'

class ModerateConfirm(TemplateView):
    template_name = 'moderation/moderate-confirm.html'