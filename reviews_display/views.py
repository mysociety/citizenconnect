from .models import Review
from django.views.generic import ListView


class ReviewsOverview(ListView):
    paginate_by = 10
    model = Review
    context_object_name = 'reviews'

    # def get(self, *args, **kwargs):
    #     super(PickProviderBase, self).get(*args, **kwargs)
    #     return render(self.request, self.form_template_name, {'form': form})
