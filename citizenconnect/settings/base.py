# Django settings for citizenconnect project.

import os
from django.conf import global_settings
from .paths import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PARENT_DIR, 'sqlite.db'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-gb'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(PARENT_DIR, 'uploads')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(PARENT_DIR, 'collected_static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, 'web'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'reversion.middleware.RevisionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'organisations.middleware.SuperuserLogEntryMiddleware',
    'failedloginblocker.middleware.FailedLoginBlockerMiddleware',
)

ROOT_URLCONF = 'citizenconnect.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'citizenconnect.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_DIR, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    "django.core.context_processors.request",
    "citizenconnect.context_processors.add_settings",
    "citizenconnect.context_processors.add_cobrand",
    "citizenconnect.context_processors.add_site_section",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.gis',
    'django_tables2',
    'south',
    'sorl.thumbnail',
    'citizenconnect',
    'pagination',
    'organisations',
    'issues',
    'reviews_submit',
    'reviews_display',
    'moderation',
    'api',
    'responses',
    'reversion',
    'failedloginblocker',
    'geocoder',
)


# Only test some of the apps by default. Anything in INSTALLED_APPS starting
# 'django' is ignored and you can add additional apps to ignore to
# IGNORE_APPS_FOR_TESTING
IGNORE_APPS_FOR_TESTING = ('south', 'pagination', 'reversion')
TEST_RUNNER = 'citizenconnect.tests.runner.AppsTestSuiteRunner'


# Log WARN and above to stderr; ERROR and above by email when DEBUG is False.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'WARN',
            'class': 'logging.StreamHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        '': {
            'handlers': ['mail_admins', 'console'],
            'level': 'WARN',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'WARN',
            'propagate': True,
        },
    }
}

# pagination related settings
PAGINATION_DEFAULT_PAGINATION = 10
PAGINATION_DEFAULT_WINDOW = 2
PAGINATION_DEFAULT_ORPHANS = 2
PAGINATION_INVALID_PAGE_RAISES_404 = True

# Authentication related settings
LOGIN_URL = '/private/login'
# We have to set this to something otherwise Django will redirect
# to /accounts/profile (which doesn't exist) if next is not specified
# on any login_required urls
LOGIN_REDIRECT_URL = '/private/'
# Makes sense to have this as a setting too
LOGOUT_REDIRECT_URL = '/'

# Password related settings - see https://github.com/dstufft/django-passwords
# and our derived PasswordField implementation for details. Note that
# PASSWORD_DICTIONARY and PASSWORD_MATCH_THRESHOLD are ommited as they cause
# the validation to be extreemly slow ( >5s per password on a fast dev box)
PASSWORD_MIN_LENGTH = 10
PASSWORD_MAX_LENGTH = None
PASSWORD_COMPLEXITY = {
    "UPPER": 1,
    "LOWER": 1,
    "DIGITS": 1,
    "PUNCTUATION": 1,
}

# Failed login blocker configuration
FLB_MAX_FAILURES = 3
FLB_BLOCK_INTERVAL = 60 # minutes

AUTHENTICATION_BACKENDS = (
    'failedloginblocker.backends.MonitoredModelBackend',
)

# Where should the geocoder load data for?
GEOCODER_BOUNDING_BOXES=(
    # xmin,  ymin,  xmax,  ymax
    ( -0.75, 51.29, 0.57,  51.72 ), # London
    ( -2.28, 54.75, -0.96, 55.15 ), # North East

)

# Now get the mySociety configuration
from .mysociety import *






