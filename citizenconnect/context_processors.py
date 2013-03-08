import os

from django.conf import settings
from django.core.urlresolvers import resolve

def add_settings( request ):
    """Add some selected settings values to the context"""
    return {
        'settings': {
            'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
        }
    }

def add_cobrand( request ):
    """Add a cobrand if one is indicated by the url"""
    func, args, kwargs = resolve(request.path)
    cobrand_info = {}
    if 'cobrand' in kwargs:
        cobrand = kwargs['cobrand']
        return {
            'cobrand': {
                'name': cobrand,
                'stylesheet' : "css/%s.css" % cobrand,
                'header_template' : "%s/header.html" % cobrand,
                'footer_template' : "%s/footer.html" % cobrand
            }
        }
    else:
        return {}
