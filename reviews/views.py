# Django imports
from django.views.generic import FormView, TemplateView

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase

class PickProvider(PickProviderBase):
    result_link_url_name = 'reviews-pick-provider'

class ReviewForm(TemplateView):
    template_name = 'reviews/review-form.html'
    choices_id = None
    org_type = None

class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'
