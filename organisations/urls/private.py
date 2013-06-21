from django.conf.urls import patterns, url
from django.conf import settings
from django.contrib.auth.decorators import login_required

from reviews_display.views import ReviewTrustList

from organisations.views.base import *
from organisations.views.organisations import *
from organisations.views.trusts import *
from organisations.views.ccgs import *
from organisations.auth import StrongSetPasswordForm, StrongPasswordChangeForm

urlpatterns = patterns(
    '',

    # Trust urls
    url(r'^trust/(?P<code>\w+)/dashboard$',
        login_required(OrganisationParentDashboard.as_view()),
        name='trust-dashboard',
        kwargs={'private': True}),

    url(r'^trust/(?P<code>\w+)/summary$',
        login_required(OrganisationParentSummary.as_view()),
        name='trust-summary',
        kwargs={'private': True}),

    url(r'^trust/(?P<code>\w+)/problems$',
        login_required(OrganisationParentProblems.as_view()),
        name='trust-problems',
        kwargs={'private': True}),

    url(r'^trust/(?P<code>\w+)/reviews$',
        login_required(ReviewTrustList.as_view()),
        name='trust-reviews',
        kwargs={'private': True}),

    url(r'^trust/(?P<code>\w+)/breaches$',
        login_required(OrganisationParentBreaches.as_view()),
        name='trust-breaches',
        kwargs={'private': True}),

    # CCG urls
    url(r'^ccg/(?P<code>\w+)/dashboard$',
        login_required(CCGDashboard.as_view()),
        name='ccg-dashboard',
        kwargs={'private': True}),

    url(r'^ccg/(?P<code>\w+)/escalation$',
        login_required(CCGEscalationDashboard.as_view()),
        name='ccg-escalation-dashboard',
        kwargs={'private': True}),

    url(r'^ccg/(?P<code>\w+)/breaches$',
        login_required(CCGEscalationBreaches.as_view()),
        name='ccg-escalation-breaches',
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

    # Body-independent urls
    url(r'^summary$',
        login_required(PrivateNationalSummary.as_view()),
        name='private-national-summary',
        kwargs={'private': True}),

    url(r'^access-logs$',
        login_required(SuperuserLogs.as_view()),
        name='superuser-logs'),

    url(r'^escalation$',
        login_required(EscalationDashboard.as_view()),
        name='escalation-dashboard',
        kwargs={'private': True}),

    url(r'^escalation/breaches$',
        login_required(EscalationBreaches.as_view()),
        name='escalation-breaches',
        kwargs={'private': True}),

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

    # Page which redirects a user to the right place after logging in
    url(r'^login-redirect$', login_redirect, name='login_redirect'),

)
