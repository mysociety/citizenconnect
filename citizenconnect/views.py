from citizenconnect.shortcuts import render

# Django imports
from django.views.generic import TemplateView

class Home(TemplateView):
    template_name = 'index.html'

class CobrandChoice(TemplateView):
    template_name = 'cobrand_choice.html'

class About(TemplateView):
    template_name = 'about.html'
