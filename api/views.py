from django.views.generic import CreateView
from django.http import HttpResponse
from django.utils import simplejson as json
from django.core.files.images import ImageFile

from issues.models import Problem

from .forms import ProblemAPIForm


class APIProblemCreate(CreateView):
    model = Problem
    form_class = ProblemAPIForm

    # Limit this view to POST requests, we don't want to show an HTML form for it
    http_method_names = ['post']

    def render_to_json_response(self, context, **kwargs):
        kwargs['content_type'] = 'application/json'
        return HttpResponse(context, **kwargs)

    # On success, return a JSON object instead of redirecting
    def form_valid(self, form):
        # Save the form
        self.object = form.save()

        # Attach images to problem if provided.
        if form.cleaned_data['images_0']:
            self.object.images.create(image=ImageFile(form.cleaned_data['images_0']))

        if form.cleaned_data['images_1']:
            self.object.images.create(image=ImageFile(form.cleaned_data['images_1']))

        if form.cleaned_data['images_2']:
            self.object.images.create(image=ImageFile(form.cleaned_data['images_2']))

        # Return a 201 with JSON

        # Make custom json because we need to return the reference_number
        # which is a computed property that django's serializers don't
        # understand
        serialised = json.dumps({'reference_number': self.object.reference_number})

        response = self.render_to_json_response(serialised)
        response.status_code = 201
        return response

    # On error, return the errors
    def form_invalid(self, form):
        response = self.render_to_json_response(json.dumps({ 'errors': json.dumps(form.errors) }))
        response.status_code = 400
        return response
