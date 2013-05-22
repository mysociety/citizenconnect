# Django imports
from django.views.generic import FormView, TemplateView
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

# App imports
from citizenconnect.shortcuts import render
from organisations.views import PickProviderBase
from organisations.models import Organisation
from .models import Review, Rating, Question
from . import forms


class PickProvider(PickProviderBase):
    result_link_url_name = 'review-form'


class ReviewForm(CreateView):
    template_name = 'reviews/review-form.html'
    form_class = forms.ReviewForm

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.cobrand = kwargs['cobrand']
        self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        self.questions = Question.objects.filter(org_type=self.organisation.organisation_type)
        return super(ReviewForm, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('review-confirm', kwargs={'cobrand': self.cobrand, 'ods_code': self.organisation.ods_code})

    def get_object(self):
        return Review(organisation=self.organisation)

    def get_context_data(self, **kwargs):
        context = super(ReviewForm, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation
        context['rating_forms'] = forms.ratings_forms_for_review(self.get_object(), self.request, self.questions)

        return context

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return form_class(**kwargs)

    def form_valid(self, form):
        review = form.save()
        rating_forms = forms.ratings_forms_for_review(review, self.request, self.questions)
        for rating_form in rating_forms:
            if not rating_form.is_valid():
                return self.render_to_response(self.get_context_data(form=form))

            rating_form.save()
        return HttpResponseRedirect(self.get_success_url())


class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewConfirm, self).get_context_data(**kwargs)
        context['organisation'] = Organisation.objects.get(ods_code=context['params']['ods_code'])
        return context
