# Django imports
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


# App imports
from issues.forms import LookupForm
from issues.models import Problem
from reviews_display.models import Review

class Home(FormView):
    template_name = 'index.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        problem_url = reverse("problem-view", kwargs={'pk': form.cleaned_data['model_id'],
                                                       'cobrand': self.kwargs['cobrand']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(problem_url)

    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        num_issues = 5
        problems = Problem.objects.all_moderated_published_problems().order_by('-created')[:num_issues]
        reviews = Review.objects.all().order_by('-api_published')[:num_issues]

        # Merge and reverse date sort, getting most recent from merged list
        issues = (list(problems) + list(reviews))
        date_created = lambda issue: issue.api_published if hasattr(issue,'api_published') else issue.created
        issues.sort(key=date_created, reverse=True)
        context['issues'] = issues[:num_issues]

        return context

class CobrandChoice(TemplateView):
    template_name = 'cobrand_choice.html'

class About(TemplateView):
    template_name = 'about.html'
