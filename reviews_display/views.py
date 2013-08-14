
from django.views.generic import DetailView, TemplateView
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist


from django_tables2 import RequestConfig

from organisations.views.organisations import OrganisationAwareViewMixin
from organisations.views.organisation_parents import OrganisationParentAwareViewMixin

from .models import Review
from .tables import ReviewTable, OrganisationParentReviewTable


class ReviewLoadOrganisationBase(OrganisationAwareViewMixin):

    def get_queryset(self):
        return self.organisation.reviews.filter(api_category="comment")


class ReviewOrganisationList(OrganisationAwareViewMixin,
                             TemplateView):
    """ All the reviews for a given organisation """

    template_name = 'reviews_display/reviews_organisation_list.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewOrganisationList, self).get_context_data(**kwargs)
        all_reviews = self.organisation.reviews.all().filter(in_reply_to=None).order_by('-api_published')
        table = ReviewTable(
            data=all_reviews,
            organisation=self.organisation,
            cobrand=kwargs['cobrand']
        )
        RequestConfig(self.request, paginate={'per_page': 8}).configure(table)
        context['table'] = table
        context['page_obj'] = table.page
        context['total_reviews'] = all_reviews.count()
        return context


class OrganisationParentReviews(OrganisationParentAwareViewMixin,
                                TemplateView):
    """ All the reviews for a given organisation parent """

    template_name = 'reviews_display/organisation_parent_reviews.html'

    def get_context_data(self, **kwargs):
        context = super(OrganisationParentReviews, self).get_context_data(**kwargs)
        # Note we distinct() the results here because we're getting the reviews
        # via their associated organisations' parent, and for GP surgeries, this
        # would otherwise mean that they saw the same review duplicated for every branch
        all_reviews = Review.objects.all().filter(
            organisations__parent=self.organisation_parent,
            in_reply_to=None
        ).order_by('-api_published').distinct()
        table = OrganisationParentReviewTable(all_reviews)
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
