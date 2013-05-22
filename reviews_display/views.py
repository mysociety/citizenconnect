
from django.views.generic import DetailView, TemplateView
from django_tables2 import RequestConfig

from .tables import ReviewTable
from organisations.views import OrganisationAwareViewMixin


class ReviewLoadOrganisationBase(OrganisationAwareViewMixin):

    def get_queryset(self):
        return self.organisation.reviews.filter(api_category="comment")


class ReviewOrganisationList(OrganisationAwareViewMixin,
                             TemplateView):
    template_name = 'reviews_display/reviews_organisation_list.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewOrganisationList, self).get_context_data(**kwargs)
        all_reviews = self.organisation.reviews.all()
        table = ReviewTable(all_reviews)
        RequestConfig(self.request, paginate={'per_page': 8}).configure(table)
        context['table'] = table
        context['page_obj'] = table.page
        context['total_reviews'] = all_reviews.count()
        return context


class ReviewDetail(ReviewLoadOrganisationBase, DetailView):
    pass
