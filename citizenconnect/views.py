# Django imports
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.forms.widgets import HiddenInput
from django.template import RequestContext
from django.core.urlresolvers import reverse

# App imports
from citizenconnect.shortcuts import render
from organisations.models import Organisation, Service

class Home(TemplateView):
    template_name = 'index.html'

class CobrandChoice(TemplateView):
    template_name = 'cobrand_choice.html'

class About(TemplateView):
    template_name = 'about.html'

class MessageCreateViewMixin(object):

    def get_success_url(self):
        # Get the request context (ie: run our context processors)
        # So that we know what cobrand to use
        context = RequestContext(self.request)
        return reverse(self.confirm_url, kwargs={'cobrand':context["cobrand"]["name"]})

    def get_initial(self):
        initial = super(MessageCreateViewMixin, self).get_initial()
        initial = initial.copy()
        self.organisation = get_object_or_404(Organisation, ods_code=self.kwargs['ods_code'])
        initial['organisation'] = self.organisation
        return initial

    def get_form(self, form_class):
        form = super(MessageCreateViewMixin, self).get_form(form_class)
        services = Service.objects.filter(organisation=self.organisation).order_by('name')
        if len(services) == 0:
            form.fields['service'].widget = HiddenInput()
        else:
            form.fields['service'].queryset = services
        return form
