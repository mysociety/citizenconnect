
from django.views.generic import ListView, DetailView, TemplateView
from django_tables2 import RequestConfig

from .models import Review
from .tables import ReviewTable
from organisations.views import OrganisationAwareViewMixin


class ReviewList(ListView):
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'


class ReviewLoadOrganisationBase(OrganisationAwareViewMixin):

    def get_queryset(self):
        return self.organisation.reviews.all()


class ReviewOrganisationList(OrganisationAwareViewMixin,
                             TemplateView):
    template_name = 'reviews_display/reviews_organisation_list.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewOrganisationList, self).get_context_data(**kwargs)
        table = ReviewTable(self.organisation.reviews.all())
        RequestConfig(self.request, paginate={'per_page': 8}).configure(table)
        context['table'] = table
        context['page_obj'] = table.page
        return context


class ReviewDetail(ReviewLoadOrganisationBase, DetailView):
    pass
