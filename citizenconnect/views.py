from citizenconnect.shortcuts import render

# Django imports
from django.views.generic import TemplateView

class Home(TemplateView):
    template_name = 'index.html'
