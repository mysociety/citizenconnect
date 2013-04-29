# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase
from organisations.models import Organisation
from .models import Question


class PickProvider(PickProviderBase):
    result_link_url_name = 'review-form'


class ReviewForm(TemplateView):
    template_name = 'reviews/review-form.html'
    choices_id = None
    org_type = None

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        return super(ReviewForm, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ReviewForm, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation
        context['questions'] = Question.objects.filter(org_type=self.organisation.organisation_type)
        return context


class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'
