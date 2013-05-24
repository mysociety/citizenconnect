# Django imports
from django.views.generic import TemplateView, View, RedirectView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template.loader import get_template
from django.core import mail
from django.template import Context


# App imports
from issues.forms import PublicLookupForm, FeedbackForm
from issues.models import Problem
from reviews_display.models import Review

class Home(FormView):
    template_name = 'index.html'
    form_class = PublicLookupForm

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

class DevHomepageSelector(TemplateView):
    template_name = 'dev-homepage.html'
    redirect_url = reverse_lazy('home', kwargs={'cobrand': settings.ALLOWED_COBRANDS[0]})

    def get(self, request, *args, **kwargs):
        if settings.STAGING:
            return super(DevHomepageSelector, self).get(request, *args, **kwargs)
        else:
            return HttpResponsePermanentRedirect(self.redirect_url)

class About(TemplateView):
    template_name = 'about.html'

class Feedback(FormView):
    template_name = 'feedback_form.html'
    form_class = FeedbackForm

    def form_valid(self, form):
        feedback_template = get_template('feedback_email.txt')

        context = Context({
            'feedback_comments': form.cleaned_data['feedback_comments'],
            'name': form.cleaned_data['name'],
            'email': form.cleaned_data['email']})

        subject = "Feedback on CareConnect Service from {0}".format(form.cleaned_data['name'])
        message = feedback_template.render(context)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipients = [settings.FEEDBACK_EMAIL_ADDRESS]

        mail.send_mail(subject, message, from_email, recipients)
        return HttpResponseRedirect(reverse('feedback-confirm', kwargs={'cobrand': self.kwargs['cobrand']}))


class FeedbackConfirm(TemplateView):
    template_name = 'feedback_confirm.html'
