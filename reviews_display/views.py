
from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from .models              import Review
from organisations.models import Organisation


class ReviewList(ListView):
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'

    # def get(self, *args, **kwargs):
    #     super(PickProviderBase, self).get(*args, **kwargs)
    #     return render(self.request, self.form_template_name, {'form': form})

class ReviewOrganisationList(ListView):
    template_name = 'reviews_display/reviews_organisation_list.html'
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'

    def get_queryset(self):
        self.organisation = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        return Review.objects.filter(organisation=self.organisation)

    def get_context_data(self, **kwargs):
            """Add organisation to the context"""
            context = super(ReviewOrganisationList, self).get_context_data(**kwargs)
            context['organisation'] = self.organisation
            return context

