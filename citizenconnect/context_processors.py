import os

from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404


def add_settings(request):
    """Add some selected settings values to the context"""
    return {
        'settings': {
            'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
            'FEEDBACK_EMAIL_ADDRESS': settings.FEEDBACK_EMAIL_ADDRESS,
            'ABUSE_EMAIL_ADDRESS': settings.ABUSE_EMAIL_ADDRESS,
            'SURVEY_INTERVAL_IN_DAYS': settings.SURVEY_INTERVAL_IN_DAYS,
        }
    }


def add_cobrand(request):
    """Add a cobrand if one is indicated by the url"""
    try:
        func, args, kwargs = resolve(request.path)
    except Resolver404:
        return {}

    if 'cobrand' in kwargs:
        cobrand = kwargs['cobrand']
        return {
            'cobrand': {
                'name': cobrand,
                'styles_template': "%s/styles.html" % cobrand,
                'scripts_template': "%s/scripts.html" % cobrand,
                'header_template': "%s/header.html" % cobrand,
                'footer_template': "%s/footer.html" % cobrand
            }
        }
    else:
        return {}


def add_site_section(request):
    """Add a site_section if one is indicated by the url"""

    path_parts = request.path.split('/') # --> ['', cobrand, section, ... ]
    try:
        cobrand = path_parts[1]
        section_url = path_parts[2]
    except IndexError:
        return {}

    known_sections = {
        # 'url_path_part': 'site_section'
        'problem': 'problem',
        'reviews': 'review',
        'common-questions': 'question',
    }

    # If the first part is a cobrand and the second a known site_section
    if cobrand in settings.ALLOWED_COBRANDS:
        site_section = known_sections.get(section_url)
        if site_section:
            return { 'site_section': site_section }

    # Fall through to not adding anything to the context
    return {}
