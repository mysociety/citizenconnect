from django.conf.urls import patterns, url
from django.conf import settings
from django.contrib.auth.decorators import login_required

from reviews_display.views import OrganisationParentReviews
from issues.views import OrganisationParentProblems, OrganisationParentBreaches

from organisations.views.base import *
from organisations.views.organisations import *
from organisations.views.organisation_parents import *
from organisations.views.ccgs import *
from organisations.views.superusers import *
from organisations.auth import StrongSetPasswordForm, StrongPasswordChangeForm

urlpatterns = patterns(
    '',

    url(r'^$',
        login_required(PrivateHome.as_view()),
        name='private_home'),

    # Organisation Parent urls
    url(r'^org-parent/(?P<code>\w+)/dashboard$',
        login_required(OrganisationParentDashboard.as_view()),
        name='org-parent-dashboard',
        kwargs={'private': True}),

    url(r'^org-parent/(?P<code>\w+)/summary$',
        login_required(OrganisationParentSummary.as_view()),
        name='org-parent-summary',
        kwargs={'private': True}),

    url(r'^org-parent/(?P<code>\w+)/problems$',
        login_required(OrganisationParentProblems.as_view()),
        name='org-parent-problems',
        kwargs={'private': True}),

    url(r'^org-parent/(?P<code>\w+)/reviews$',
        login_required(OrganisationParentReviews.as_view()),
        name='org-parent-reviews',
        kwargs={'private': True}),

    url(r'^org-parent/(?P<code>\w+)/breaches$',
        login_required(OrganisationParentBreaches.as_view()),
        name='org-parent-breaches',
        kwargs={'private': True}),

    url(r'^org-parent/(?P<code>\w+)/surveys$',
        login_required(OrganisationParentSurveys.as_view()),
        name='org-parent-surveys',
        kwargs={'private': True}),

    # CCG urls
    url(r'^ccg/(?P<code>\w+)/dashboard$',
        login_required(CCGDashboard.as_view()),
        name='ccg-dashboard',
        kwargs={'private': True}),

    url(r'^ccg/(?P<code>\w+)/summary$',
        login_required(CCGSummary.as_view()),
        name='ccg-summary',
        kwargs={'private': True}),

    # Organisation urls
    url(r'^organisation/(?P<ods_code>\w+)/summary$',
        login_required(OrganisationSummary.as_view()),
        name='private-org-summary',
        kwargs={'private': True}),

    # Superuser urls
    url(r'^superuser/dashboard$',
        login_required(SuperuserDashboard.as_view()),
        name='superuser-dashboard'),

    url(r'^superuser/access-logs$',
        login_required(SuperuserLogs.as_view()),
        name='superuser-logs'),

    url(r'^superuser/problems-csv$',
        login_required(ProblemsCSV.as_view()),
        name='problems-csv'),

    # Authentication related urls
    url(r'^login$',
        'django.contrib.auth.views.login',
        name='login',
        kwargs={'template_name': 'organisations/auth/login.html'}),

    url(r'^logout$',
        'django.contrib.auth.views.logout',
        name='logout',
        kwargs={'next_page': settings.LOGOUT_REDIRECT_URL}),

    url(r'^password-reset$',
        'django.contrib.auth.views.password_reset',
        name='password_reset',
        kwargs={
            'template_name': 'organisations/auth/password_reset_form.html',
            'email_template_name': 'organisations/auth/password_reset_email.txt',
            'subject_template_name': 'organisations/auth/password_reset_subject.txt'
        }),

    url(r'^password-reset-done$',
        'django.contrib.auth.views.password_reset_done',
        name='password_reset_done',
        kwargs={'template_name': 'organisations/auth/password_reset_done.html'}),

    url(
        r'^password-reset-confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm',
        kwargs={
            'template_name': 'organisations/auth/password_reset_confirm.html',
            'set_password_form': StrongSetPasswordForm,
        }
    ),

    url(r'^password-reset-complete$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete',
        kwargs={'template_name': 'organisations/auth/password_reset_complete.html'}),

    url(
        r'^password-change$',
        'django.contrib.auth.views.password_change',
        name='password_change',
        kwargs={
            'template_name': 'organisations/auth/password_change_form.html',
            'password_change_form': StrongPasswordChangeForm,
        }
    ),

    url(r'^password-change-done$',
        'django.contrib.auth.views.password_change_done',
        name='password_change_done',
        kwargs={'template_name': 'organisations/auth/password_change_done.html'}),

)
