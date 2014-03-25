from datetime import datetime, date, time, timedelta

# Django imports
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template.loader import get_template
from django.core import mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import Context
from django.utils import timezone

from django.contrib.auth.models import User

# App imports
from issues.forms import PublicLookupForm
from issues.models import Problem
from reviews_display.models import Review
from reviews_submit.models import Review as SubmittedReview
from news.models import Article

from .forms import LiveFeedFilterForm, FeedbackForm


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
        initial['start'] = date.today() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS)
        initial['end'] = date.today()
        return initial

    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}

        # Pass form kwargs from GET instead of POST
        if self.request.GET:
            # We pop the page GET variable because otherwise the form will
            # ignore initial data just because you specified a page
            data = self.request.GET.copy()
            data.pop('page', None)
            if data:
                kwargs['data'] = data
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
            start_date = date.today() - timedelta(days=settings.LIVE_FEED_CUTOFF_DAYS)
        # We have to make this a timezone-aware datetime to keep the ORM happy
        start_datetime = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        context['cutoff_date'] =  start_datetime
        problems = problems.filter(created__gte=start_datetime)
        reviews = reviews.filter(api_published__gte=start_datetime)

        # End date
        if filters.get('end'):
            end_date = filters['end']
            # We also have to make this a timezone-aware datetime to keep the ORM happy
            end_datetime = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
            problems = problems.filter(created__lte=end_datetime)
            reviews = reviews.filter(api_published__lte=end_datetime)

        # Organisation
        if filters.get('organisation'):
            organisation = filters['organisation']
            problems = problems.filter(organisation=organisation)
            reviews = reviews.filter(organisations=organisation)

        # Merge and reverse date sort, getting most recent from merged list
        # TODO - this is really inefficient and will probably take a long
        # time for large date ranges, perhaps we need to rewrite the whole
        # thing as custom SQL one day to avoid merging/sorting these two lists...
        issues = (list(problems) + list(reviews))
        date_created = lambda issue: issue.api_published if hasattr(issue, 'api_published') else issue.created
        issues.sort(key=date_created, reverse=True)

        # Deal with pagination
        paginator = Paginator(issues, settings.LIVE_FEED_PER_PAGE)
        page = self.request.GET.get('page', 1)
        try:
            issues = paginator.page(page)
        except PageNotAnInteger:
            issues = paginator.page(1)
        except EmptyPage:
            issues = paginator.page(paginator.num_pages)

        context['issues'] = issues
        context['page_obj'] = issues
        context['page_numbers'] = paginator.page_range

        return context


class HealthCheck(TemplateView):

    template_name = 'citizenconnect/health_check.html'

    # Default response status, we'll alter this if there's something unhealthy
    # that we wish to report as an error
    status = 200

    def render_to_response(self, context, **response_kwargs):
        """Override render_to_response so that we can control the HTTP status"""

        response_kwargs['status'] = self.status

        return super(TemplateView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super(HealthCheck, self).get_context_data(**kwargs)

        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        two_hours_ago = now - timedelta(hours=2)
        two_days_ago = now - timedelta(days=2)
        one_week_ago = now - timedelta(days=2)

        # Unsent problems
        unsent_problems = Problem.objects.filter(
            created__lte=two_hours_ago,
            mailed=False
        )
        context['unsent_problems'] = unsent_problems
        context['unsent_problems_healthy'] = True

        if unsent_problems:
            self.status = 500
            context['unsent_problems_healthy'] = False

        # Unsent confirmations
        unsent_confirmations = Problem.objects.requiring_confirmation().filter(
            created__lte=two_hours_ago
        )
        context['unsent_confirmations'] = unsent_confirmations
        context['unsent_confirmations_healthy'] = True

        if unsent_confirmations:
            self.status = 500
            context['unsent_confirmations_healthy'] = False

        # Unsent surveys
        unsent_surveys = list(Problem.objects.requiring_survey_to_be_sent())
        # These are a bit trickier because we don't have a timestamp for when
        # they are closed, which is the key piece of information to see if
        # the email sending is late. To find this out, we inspect the revision
        # history to find any that were closed more than two hours ago.
        for problem in unsent_surveys:
            if problem.closed_timestamp >= two_hours_ago:
                unsent_surveys.remove(problem)
        context['unsent_surveys'] = unsent_surveys
        context['unsent_surveys_healthy'] = True

        if unsent_surveys:
            self.status = 500
            context['unsent_surveys_healthy'] = False

        # Unsent reviews
        unsent_reviews = SubmittedReview.objects.filter(
            last_sent_to_api__isnull=True,
            created__lte=two_hours_ago
        )
        context['unsent_reviews'] = unsent_reviews
        context['unsent_reviews_healthy'] = True

        if unsent_reviews:
            self.status = 500
            context['unsent_reviews_healthy'] = False

        # No new reviews from the choices api
        latest_choices_reviews = Review.objects.all().order_by('-created')
        if latest_choices_reviews:
            context['latest_choices_review'] = latest_choices_review = latest_choices_reviews[0]
            context['latest_choices_review_healthy'] = True
            if latest_choices_review.created <= two_days_ago:
                self.status = 500
                context['latest_choices_review_healthy'] = False

        # No new problems
        latest_problems = Problem.objects.all().order_by('-created')
        if latest_problems:
            context['latest_problem'] = latest_problem = latest_problems[0]
            context['latest_problem_healthy'] = True
            if latest_problem.created <= one_week_ago:
                self.status = 500
                context['latest_problem_healthy'] = False

        return context
