# Django imports
from django.views.generic import TemplateView

class ModerateHome(TemplateView):
    template_name = 'moderation/moderate-home.html'

class ModerateLookup(TemplateView):
    template_name = 'moderation/moderate-lookup.html'

class ModerateForm(TemplateView):
    template_name = 'moderation/moderate-form.html'

class ModerateConfirm(TemplateView):
    template_name = 'moderation/moderate-confirm.html'