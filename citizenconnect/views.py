from datetime import datetime, date, timedelta

# Django imports
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template.loader import get_template
from django.core import mail
from django.template import Context
from django.utils.timezone import utc

from django.contrib.auth.models import User

# App imports
from issues.forms import PublicLookupForm, FeedbackForm
from issues.models import Problem
from reviews_display.models import Review
from news.models import Article

from .forms import LiveFeedFilterForm


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


class LiveFeed(FormView):
    """A list of all the recent problems and reviews in the system."""

    template_name = 'citizenconnect/live_feed.html'
    form_class = LiveFeedFilterForm

    # TODO: the get, get_initial and get_form_kwargs bits of this are
    # basically copy and pasted from organisations.FilterFormMixin - perhaps
    # we need to refactor some of them into a more generic GETFormMixin, since
    # that's what they're really doing.

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        # Note: we call this to get a cleaned_data dict, which we then
        # pass on into the context for use in filtering, but we don't
        # care if it fails, because then it won't go into the context
        # and the views can just ignore any duff selections
        form.is_valid()
        kwargs['form'] = form
        return self.render_to_response(self.get_context_data(**kwargs))

    def get_initial(self):
        initial = super(LiveFeed, self).get_initial()
        initial['start_date'] = datetime.now(utc).date() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS)
        return initial

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}

        # Calculate a useful range of years to allow selection from
        this_year = date.today().year
        oldest_problem = Problem.objects.all().order_by('created')[0]
        oldest_review = Review.objects.all().order_by('api_published')[0]
        if oldest_review.api_published >= oldest_problem.created:
            oldest_year = oldest_review.api_published.year
        else:
            oldest_year = oldest_problem.created.year
        kwargs['years'] = range(oldest_year, this_year + 1)

        # Pass form kwargs from GET instead of POST
        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def build_filters(self, form):
        """Build a filter dictionary from the form"""
        filters = {}
        if hasattr(form, 'cleaned_data'):
            if form.cleaned_data.get('organisation'):
                filters['organisation'] = form.cleaned_data.get('organisation')
            if form.cleaned_data.get('start'):
                filters['start'] = form.cleaned_data.get('start')
            if form.cleaned_data.get('end'):
                filters['end'] = form.cleaned_data.get('end')
        return filters

    def get_context_data(self, **kwargs):
        context = super(LiveFeed, self).get_context_data(**kwargs)

        # Get base queryset of problems and reviews
        # Problems - we have to show all problems that are either open or
        # closed, but we don't want things that have been completely removed
        # (publication_status=REJECTED) or that are awaiting complicated legal
        # moderation.
        problems = Problem.objects.all_not_rejected_visible_problems().order_by('-created')
        reviews = Review.objects.all().filter(in_reply_to=None).order_by('-api_published')

        filters = self.build_filters(context['form'])

        # Apply filters
        # Start date
        if filters.get('start'):
            start_date = filters['start']
        else:
            # We default to showing only some problems regardless
            start_date = datetime.now(utc).date() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS)
        context['cutoff_date'] =  start_date
        problems = problems.filter(created__gte=start_date)
        reviews = reviews.filter(created__gte=start_date)

        # End date
        if filters.get('end'):
            end_date = filters['end']
            problems = problems.filter(created__lte=end_date)
            reviews = reviews.filter(created__lte=end_date)

        # Organisation
        if filters.get('organisation'):
            organisation = filters['organisation']
            problems = problems.filter(organisation=organisation)
            reviews = reviews.filter(organisations=organisation)

        # Merge and reverse date sort, getting most recent from merged list
        issues = (list(problems) + list(reviews))
        date_created = lambda issue: issue.api_published if hasattr(issue, 'api_published') else issue.created
        issues.sort(key=date_created, reverse=True)

        context['issues'] = issues

        return context

