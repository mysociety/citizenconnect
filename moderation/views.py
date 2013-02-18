from itertools import chain
from operator import attrgetter

# Django imports
from django.views.generic import TemplateView, UpdateView
from django.views.generic.edit import FormView
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

# App imports
from problems.models import Problem
from questions.models import Question

from .forms import LookupForm

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

class ModerateLookup(FormView):
    template_name = 'moderation/moderate-lookup.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        context = RequestContext(self.request)
        moderate_url = reverse("moderate-form", kwargs={'message_type': form.cleaned_data['model_type'],
                                                        'pk': form.cleaned_data['model_id']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(moderate_url)


class ModerateForm(UpdateView):
    model = Problem
    template_name = 'moderation/moderate-form.html'

    def get_context_data(self, **kwargs):
        context = super(ModerateForm, self).get_context_data(**kwargs)
        # Get the problem or question
        message_type = self.kwargs['message_type']
        if message_type == 'question':
            context['message'] = Question.objects.get(id=self.kwargs['pk'])
        elif message_type == 'problem':
            context['message'] = Problem.objects.get(id=self.kwargs['pk'])
        else:
            raise ValueError("Unknown message type: %s" % message_type)
        return context

class ModerateConfirm(TemplateView):
    template_name = 'moderation/moderate-confirm.html'