# Django imports
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect


# App imports
from issues.forms import LookupForm

class Home(FormView):
    template_name = 'index.html'
    form_class = LookupForm

    def form_valid(self, form):
        # Calculate the url
        problem_url = reverse("problem-view", kwargs={'pk': form.cleaned_data['model_id'],
                                                       'cobrand': self.kwargs['cobrand']})
        # Redirect to the url we calculated
        return HttpResponseRedirect(problem_url)

class CobrandChoice(TemplateView):
    template_name = 'cobrand_choice.html'

class About(TemplateView):
    template_name = 'about.html'
