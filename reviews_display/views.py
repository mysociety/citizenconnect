
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404

from .models              import Review
from organisations.models import Organisation


class ReviewList(ListView):
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'


class ReviewLoadOrganisationBase(object):

    def get(self, request, *args, **kwargs):
        self.organisation = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        return super(ReviewLoadOrganisationBase, self).get(request, *args, **kwargs)

    def get_queryset(self):
        return self.organisation.review_set.all()

    def get_context_data(self, **kwargs):
            """Add organisation to the context"""
            context = super(ReviewLoadOrganisationBase, self).get_context_data(**kwargs)
            context['organisation'] = self.organisation
            return context


class ReviewOrganisationList(ReviewLoadOrganisationBase, ListView):
    template_name = 'reviews_display/reviews_organisation_list.html'
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'


class ReviewDetail(ReviewLoadOrganisationBase, DetailView):
    pass
