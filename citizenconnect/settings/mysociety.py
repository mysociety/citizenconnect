# load the mySociety config from its special file

import yaml
from .paths import *

config = yaml.load(open(os.path.join(PROJECT_ROOT, 'conf', 'general.yml')))

DEBUG = bool(int(config.get('STAGING')))
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config.get('CITIZENCONNECT_DB_NAME'),
        'USER': config.get('CITIZENCONNECT_DB_USER'),
        'PASSWORD': config.get('CITIZENCONNECT_DB_PASS'),
        'HOST': config.get('CITIZENCONNECT_DB_HOST'),
        'PORT': config.get('CITIZENCONNECT_DB_PORT'),
    }
}

TIME_ZONE = config.get('TIME_ZONE')
SECRET_KEY = config.get('DJANGO_SECRET_KEY')
GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')

NHS_CHOICES_API_KEY = config.get('NHS_CHOICES_API_KEY')
NHS_CHOICES_BASE_URL = config.get('NHS_CHOICES_BASE_URL')

ALLOWED_COBRANDS = config.get('ALLOWED_COBRANDS')

ORGANISATION_CHOICES = config.get('ORGANISATION_CHOICES')

ORGANISATION_TYPES = [organisation_type for organisation_type, label in ORGANISATION_CHOICES]

MAPIT_BASE_URL = config.get('MAPIT_BASE_URL')

WGS_84 = 4326

# Emails - smtp on the proper server, console when we're debugging
# so that no emails get sent from dev/staging sites to anyone important
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SITE_BASE_URL = config.get('SITE_BASE_URL')
