from django.conf.urls import patterns, url
from django.conf import settings
from django.contrib.auth.decorators import login_required

from organisations.views import *

urlpatterns = patterns('',

    url(r'^dashboard/(?P<ods_code>\w+)$',
        login_required(OrganisationDashboard.as_view()),
        name='org-dashboard',
        kwargs={'private': True}),

    url(r'^summary$',
        login_required(PrivateNationalSummary.as_view()),
        name='private-national-summary',
        kwargs={'private': True}),

    url(r'^summary/(?P<ods_code>\w+)$',
        login_required(OrganisationSummary.as_view()),
        name='private-org-summary',
        kwargs={'private': True}),

    url(r'^problems/(?P<ods_code>\w+)$',
        login_required(OrganisationProblems.as_view()),
        name='private-org-problems',
        kwargs={'private': True}),

    url(r'^choose-dashboard$', login_required(DashboardChoice.as_view()), name='dashboard-choice'),

    url(r'^access-logs$', login_required(SuperuserLogs.as_view()), name='superuser-logs'),

    url(r'^escalation$', login_required(EscalationDashboard.as_view()),
                         name='escalation-dashboard',
                         kwargs={'private': True}),

    url(r'^escalation/breaches$', login_required(EscalationBreaches.as_view()),
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

    url(r'^password-reset-confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)$',
        'django.contrib.auth.views.password_reset_confirm',
        name='password_reset_confirm',
        kwargs={'template_name': 'organisations/auth/password_reset_confirm.html'}),

    url(r'^password-reset-complete$',
        'django.contrib.auth.views.password_reset_complete',
        name='password_reset_complete',
        kwargs={'template_name': 'organisations/auth/password_reset_complete.html'}),

    url(r'^password-change$',
        'django.contrib.auth.views.password_change',
        name='password_change',
        kwargs={'template_name': 'organisations/auth/password_change_form.html'}),

    url(r'^password-change-done$',
        'django.contrib.auth.views.password_change_done',
        name='password_change_done',
        kwargs={'template_name': 'organisations/auth/password_change_done.html'}),

    # Page which redirects a user to the right place after logging in
    url(r'^login-redirect$', login_redirect, name='login_redirect'),

)
