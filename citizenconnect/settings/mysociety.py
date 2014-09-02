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

MAPIT_BASE_URL = config.get('MAPIT_BASE_URL')

WGS_84 = 4326

SITE_BASE_URL = config.get('SITE_BASE_URL')

# Base urls mapped to cobrands
# The real live urls are only used if we're not in debug mode
COBRAND_BASE_URLS = {
    'choices': SITE_BASE_URL if DEBUG else 'https://www.nhs.uk',
    'myhealthlondon': SITE_BASE_URL if DEBUG else 'https://www.myhealth.london.nhs.uk'
}

DEFAULT_FROM_EMAIL = config.get('DEFAULT_FROM_EMAIL')

SERVER_EMAIL = config.get('SERVER_EMAIL')

ADMINS = (('CitizenConnect Admins', SERVER_EMAIL),)

EMAIL_HOST = config.get('EMAIL_HOST')

EMAIL_PORT = config.get('EMAIL_PORT')

summary_threshold = config.get('SUMMARY_THRESHOLD')
if summary_threshold:
    SUMMARY_THRESHOLD = tuple(summary_threshold)
else:
    SUMMARY_THRESHOLD = None

FEEDBACK_EMAIL_ADDRESS = config.get("FEEDBACK_EMAIL_ADDRESS")

ABUSE_EMAIL_ADDRESS = config.get("ABUSE_EMAIL_ADDRESS")

GOOGLE_ANALYTICS_ACCOUNT = config.get('GOOGLE_ANALYTICS_ACCOUNT')

MAX_IMAGES_PER_PROBLEM = config.get('MAX_IMAGES_PER_PROBLEM')
ALLOWED_IMAGE_EXTENSIONS = config.get('ALLOWED_IMAGE_EXTENSIONS')


# Twitter related
TWITTER_USERNAME = config.get('TWITTER_USERNAME', 'CareConnectNHS')  # without the '@'
TWITTER_WIDGET_ID = config.get('TWITTER_WIDGET_ID', '355653879704207362')

NHS_RSS_FEED_URL = config.get('NHS_RSS_FEED_URL', 'http://news.careconnect.mysociety.org/feed/')

# Whether to prefer X_FORWARDED_HOST to HOST, should only be True for
# sites which are being proxied, hence set in general.yml where
# we know what site we're dealing with.
USE_X_FORWARDED_HOST = config.get('USE_X_FORWARDED_HOST', False)

SESSION_COOKIE_AGE = 7200  # Two hours max
SESSION_COOKIE_HTTPONLY = True  # This is the default, but just to make it explicit
SESSION_COOKIE_SECURE = not STAGING
SESSION_COOKIE_PATH = '/careconnect'

CSRF_COOKIE_SECURE = not STAGING
CSRF_COOKIE_PATH = '/careconnect'

ALLOWED_HOSTS = [] if STAGING else config.get('ALLOWED_HOSTS', [])

# What URL do the blog files live at?
# So that we can rewrite their HTML and reverse proxy them
BLOG_FILES_URL = 'http://news.careconnect.mysociety.org/files'
# What url should they be proxied to?
PROXIED_BLOG_FILES_URL = '/careconnect/news/files'

# How many day's worth of things to show on the Live feed
LIVE_FEED_CUTOFF_DAYS = config.get("LIVE_FEED_CUTOFF_DAYS")
LIVE_FEED_PER_PAGE = config.get("LIVE_FEED_PER_PAGE")

# Monitoring settings
# Each setting effectively is a deadline for a specific check, (in hours)
PROBLEMS_MUST_BE_SENT = config.get("PROBLEMS_MUST_BE_SENT", 2)
CONFIRMATIONS_MUST_BE_SENT = config.get("CONFIRMATIONS_MUST_BE_SENT", 2)
SURVEYS_MUST_BE_SENT = config.get("SURVEYS_MUST_BE_SENT", 2)
REVIEWS_MUST_BE_SENT = config.get("REVIEWS_MUST_BE_SENT", 2)
REVIEWS_MUST_BE_CREATED = config.get("REVIEWS_MUST_BE_CREATED", 24)
PROBLEMS_MUST_BE_CREATED = config.get("PROBLEMS_MUST_BE_CREATED", 168)
