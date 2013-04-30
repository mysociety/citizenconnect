# Django imports
from django.views.generic import FormView, TemplateView
from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.forms.models import inlineformset_factory

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
    choices_id = None
    org_type = None
    form_class = forms.ReviewForm

    def dispatch(self, request, *args, **kwargs):
        # Set organisation here so that we can use it anywhere in the class
        # without worrying about whether it has been set yet
        self.cobrand = kwargs['cobrand']
        self.organisation = Organisation.objects.get(ods_code=kwargs['ods_code'])
        self.questions = Question.objects.filter(org_type=self.organisation.organisation_type)
        return super(ReviewForm, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('review-confirm', kwargs={'cobrand': self.cobrand})

    def get_object(self):
        return Review(organisation=self.organisation)

    def get_context_data(self, **kwargs):
        context = super(ReviewForm, self).get_context_data(**kwargs)
        context['organisation'] = self.organisation

        RatingFormSet = inlineformset_factory(Review, Rating, form=forms.RatingForm, extra=self.questions.count())

        if self.request.POST:
            context['rating_forms'] = RatingFormSet(data=self.request.POST, instance=self.get_object())
        else:
            context['rating_forms'] = RatingFormSet(instance=self.get_object())

        return context

    def get_form(self, form_class):
        kwargs = self.get_form_kwargs()
        kwargs['questions'] = self.questions
        kwargs['instance'] = self.get_object()
        return form_class(**kwargs)

    def form_valid(self, form):
        context = self.get_context_data()
        rating_forms = context['rating_forms']
        if rating_forms.is_valid():
            self.object = form.save()
            rating_forms.instance = self.object
            rating_forms.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))


class ReviewConfirm(TemplateView):
    template_name = 'reviews/review-confirm.html'
