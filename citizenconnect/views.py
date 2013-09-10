# Django imports
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template.loader import get_template
from django.core import mail
from django.template import Context

from django.contrib.auth.models import User


# App imports
from issues.forms import PublicLookupForm, FeedbackForm
from issues.models import Problem
from reviews_display.models import Review
from news.models import Article


class Home(FormView):
    template_name = 'citizenconnect/index.html'
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
        problems = Problem.objects.all_published_visible_problems().order_by('-created')[:num_issues]
        reviews = Review.objects.all().filter(in_reply_to=None).order_by('-api_published')[:num_issues]

        # Merge and reverse date sort, getting most recent from merged list
        issues = (list(problems) + list(reviews))
        date_created = lambda issue: issue.api_published if hasattr(issue, 'api_published') else issue.created
        issues.sort(key=date_created, reverse=True)
        context['issues'] = issues[:num_issues]

        context['recent_articles'] = Article.objects.order_by('-published')[:3]

        return context


class MHLIframe(Home):
    """
    A version of the homepage with limited things on it for inclusion as an iframe.

    Used by the MyHealthLondon site.
    """
    template_name = 'citizenconnect/mhl_iframe.html'


class DevHomepageSelector(TemplateView):
    template_name = 'citizenconnect/dev-homepage.html'
    redirect_url = reverse_lazy('home', kwargs={'cobrand': settings.ALLOWED_COBRANDS[0]})

    def get(self, request, *args, **kwargs):
        if settings.STAGING:
            return super(DevHomepageSelector, self).get(request, *args, **kwargs)
        else:
            return HttpResponsePermanentRedirect(self.redirect_url)

    def get_context_data(self, **kwargs):
        context = super(DevHomepageSelector, self).get_context_data(**kwargs)
        context['users'] = User.objects.filter(last_name="Development User").order_by('username')
        return context


class About(TemplateView):
    template_name = 'citizenconnect/about.html'


class Feedback(FormView):
    template_name = 'citizenconnect/feedback_form.html'
    form_class = FeedbackForm

    def get_initial(self):
        initial = super(Feedback, self).get_initial()
        problem_ref = self.request.GET.get('problem_ref')
        if problem_ref is not None:
            problem_id = problem_ref[1:]
            if problem_id:
                try:
                    problem = Problem.objects.get(pk=problem_id)
                    initial['feedback_comments'] = "RE: Problem reference {0}\n\n".format(problem.reference_number)
                except Problem.DoesNotExist:
                    pass
        return initial

    def form_valid(self, form):
        feedback_template = get_template('citizenconnect/feedback_email.txt')

        context = Context({
            'feedback_comments': form.cleaned_data['feedback_comments'],
            'name': form.cleaned_data['name'],
            'email': form.cleaned_data['email']})

        subject = u"Feedback on CareConnect Service from {0}".format(form.cleaned_data['name'])
        message = feedback_template.render(context)
        from_email = settings.DEFAULT_FROM_EMAIL
        recipients = [settings.FEEDBACK_EMAIL_ADDRESS]

        mail.send_mail(subject, message, from_email, recipients)
        return HttpResponseRedirect(reverse('feedback-confirm', kwargs={'cobrand': self.kwargs['cobrand']}))


class FeedbackConfirm(TemplateView):
    template_name = 'citizenconnect/feedback_confirm.html'


class HelpYourNHS(TemplateView):
    template_name = 'citizenconnect/help_your_nhs.html'


class CommonQuestions(TemplateView):
    template_name = 'citizenconnect/common_questions.html'


class Boom(TemplateView):
    """ A helper view to show us what a server error looks like """

    def get(self, request, *args, **kwargs):
        raise(Exception("Boom!"))
