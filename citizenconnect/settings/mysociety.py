# load the mySociety config from its special file

import yaml
from .paths import *

config = yaml.load(open(os.path.join(PROJECT_ROOT, 'conf', 'general.yml')))

STAGING = bool(int(config.get('STAGING')))
DEBUG = STAGING
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

NHS_CHOICES_API_KEY = config.get('NHS_CHOICES_API_KEY')
NHS_CHOICES_BASE_URL = config.get('NHS_CHOICES_BASE_URL')
NHS_CHOICES_POSTING_ORGANISATION_ID = config.get('NHS_CHOICES_POSTING_ORGANISATION_ID')
NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS = config.get('NHS_CHOICES_API_MAX_REVIEW_AGE_IN_DAYS')


API_BASICAUTH_USERNAME = config.get('API_BASICAUTH_USERNAME')
API_BASICAUTH_PASSWORD = config.get('API_BASICAUTH_PASSWORD')

ALLOWED_COBRANDS = config.get('ALLOWED_COBRANDS')

ORGANISATION_CHOICES = config.get('ORGANISATION_CHOICES')

ORGANISATION_TYPES = [organisation_type for organisation_type, label in ORGANISATION_CHOICES]

MAPIT_BASE_URL = config.get('MAPIT_BASE_URL')

WGS_84 = 4326

SITE_BASE_URL = config.get('SITE_BASE_URL')

DEFAULT_FROM_EMAIL = config.get('DEFAULT_FROM_EMAIL')

SURVEY_INTERVAL_IN_DAYS = config.get('SURVEY_INTERVAL_IN_DAYS')

EMAIL_HOST = config.get('EMAIL_HOST')

EMAIL_PORT = config.get('EMAIL_PORT')

summary_threshold = config.get('SUMMARY_THRESHOLD')
if summary_threshold:
    SUMMARY_THRESHOLD = tuple(summary_threshold)
else:
    SUMMARY_THRESHOLD = None


# Email addresses for the Customer Contact Centre
CUSTOMER_CONTACT_CENTRE_EMAIL_ADDRESSES = config.get("CUSTOMER_CONTACT_CENTRE_EMAIL_ADDRESSES")

FEEDBACK_EMAIL_ADDRESS = config.get("FEEDBACK_EMAIL_ADDRESS")

ABUSE_EMAIL_ADDRESS = config.get("ABUSE_EMAIL_ADDRESS")

CHOICES_GOOGLE_ANALYTICS_ACCOUNT = config.get('CHOICES_GOOGLE_ANALYTICS_ACCOUNT')
MHL_GOOGLE_ANALYTICS_ACCOUNT = config.get('MHL_GOOGLE_ANALYTICS_ACCOUNT')

MAX_IMAGES_PER_PROBLEM = config.get('MAX_IMAGES_PER_PROBLEM')
