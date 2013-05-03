import os

from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404

def add_settings( request ):
    """Add some selected settings values to the context"""
    return {
        'settings': {
            'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
        }
    }

def add_cobrand( request ):
    """Add a cobrand if one is indicated by the url"""
    try:
        func, args, kwargs = resolve(request.path)
    except Resolver404:
        return {}

    cobrand_info = {}
    if 'cobrand' in kwargs:
        cobrand = kwargs['cobrand']
        return {
            'cobrand': {
                'name': cobrand,
                'styles_template': "%s/styles.html" % cobrand,
                'scripts_template': "%s/scripts.html" % cobrand,
                'header_template' : "%s/header.html" % cobrand,
                'footer_template' : "%s/footer.html" % cobrand
            }
        }
    else:
        return {}
