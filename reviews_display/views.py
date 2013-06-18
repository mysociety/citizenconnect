
from django.views.generic import DetailView, TemplateView
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist


from django_tables2 import RequestConfig

from organisations.views.organisations import OrganisationAwareViewMixin
from organisations.views.trusts import TrustAwareViewMixin

from .models import Review
from .tables import ReviewTable, TrustReviewTable


class ReviewLoadOrganisationBase(OrganisationAwareViewMixin):

    def get_queryset(self):
        return self.organisation.reviews.filter(api_category="comment")


class ReviewOrganisationList(OrganisationAwareViewMixin,
                             TemplateView):
    """ All the reviews for a given organisation """

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


class ReviewTrustList(TrustAwareViewMixin,
                      TemplateView):
    """ All the reviews for a given trust """

    template_name = 'reviews_display/reviews_trust_list.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewTrustList, self).get_context_data(**kwargs)
        all_reviews = Review.objects.all().filter(organisation__trust=self.trust)
        table = TrustReviewTable(all_reviews)
        RequestConfig(self.request, paginate={'per_page': 8}).configure(table)
        context['table'] = table
        context['page_obj'] = table.page
        context['total_reviews'] = all_reviews.count()
        return context


class ReviewDetail(ReviewLoadOrganisationBase, DetailView):

    def get_object(self):

        """
        Override the default to find a review using api_posting_id
        """

        api_posting_id = self.kwargs.get('api_posting_id')

        queryset = self.get_queryset()
        queryset = queryset.filter(api_posting_id=api_posting_id)

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise Http404("No %(verbose_name)s found matching the query" %
                          {'verbose_name': queryset.model._meta.verbose_name})

        return obj
