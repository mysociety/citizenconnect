
from django.views.generic import ListView, DetailView

from .models import Review
from organisations.views import OrganisationAwareViewMixin


class ReviewList(ListView):
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'


class ReviewLoadOrganisationBase(OrganisationAwareViewMixin):

    def get_queryset(self):
        return self.organisation.reviews.all()


class ReviewOrganisationList(ReviewLoadOrganisationBase, ListView):
    template_name = 'reviews_display/reviews_organisation_list.html'
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'


class ReviewDetail(ReviewLoadOrganisationBase, DetailView):
    pass
