# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase
from organisations.models import Organisation
from .models import Question
from .forms import ReviewForm, RatingFormSet


class PickProvider(PickProviderBase):
    result_link_url_name = 'review-form'


class ReviewForm(FormView):
    template_name = 'reviews/review-form.html'
    choices_id = None
    org_type = None
    form_class = ReviewForm

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        return super(ReviewForm, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewForm, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation

        if self.request.POST:
            context['rating_forms'] = RatingFormSet(data=self.request.POST)
        else:
            context['rating_forms'] = RatingFormSet()

        context['questions'] = Question.objects.filter(org_type=self.organisation.organisation_type)

        return context


class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'
