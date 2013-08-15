from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView

from .views import (
    Home,
    MHLIframe,
    DevHomepageSelector,
    About,
    Feedback,
    FeedbackConfirm,
    HelpYourNHS,
    CommonQuestions,
    Boom
)

# Admin section
from django.contrib import admin
admin.autodiscover()


allowed_cobrands = settings.ALLOWED_COBRANDS
cobrand_pattern = '(?P<cobrand>%s)' % '|'.join(allowed_cobrands)
urlpatterns = patterns(
    '',
    url(r'^' + cobrand_pattern + r'$', Home.as_view(), name='home'),
    # This page is only for myhealthlondon
    url(
        r'^myhealthlondon/iframe?$',
        MHLIframe.as_view(),
        name='mhl-iframe',
        kwargs={'cobrand': 'myhealthlondon'}
    ),

    url(r'^' + cobrand_pattern + r'/about$', About.as_view(), name='about'),
    url(r'^' + cobrand_pattern + r'/feedback$', Feedback.as_view(), name='feedback'),
    url(r'^' + cobrand_pattern + r'/feedback/confirm$', FeedbackConfirm.as_view(), name='feedback-confirm'),
    url(r'^' + cobrand_pattern + r'/help-your-nhs$', HelpYourNHS.as_view(), name='help-your-nhs'),
    url(r'^' + cobrand_pattern + r'/common-questions$', CommonQuestions.as_view(), name='common-questions'),

    url(r'^' + cobrand_pattern + r'/', include('issues.urls.public')),
    url(r'^' + cobrand_pattern + r'/reviews/', include('reviews_submit.urls')),
    url(r'^' + cobrand_pattern + r'/reviews', include('reviews_display.urls')),
    url(r'^' + cobrand_pattern + r'/', include('organisations.urls.public')),
    url(r'^' + cobrand_pattern + r'/news', include('news.urls')),

    # private is the namespace for NHS-staff only pages
    url(r'^private/', include('organisations.urls.private')),
    url(r'^private/moderate/', include('moderation.urls')),
    url(r'^private/response/', include('responses.urls')),

    # geocoder
    url(r'^geocoder/', include('geocoder.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # Dev page for exception handling
    url(r'^dev/boom$', Boom.as_view(), name='dev-boom'),
)

# Append /careconnect to everything above, to fix proxy relative link issues
urlpatterns = patterns(
    '',
    url(r'careconnect/', include(urlpatterns)),
)

# API links
urlpatterns += patterns(
    '',
    url(r'^api/v0.1/', include('api.urls')),
)

# Dev pages live at the real root though
urlpatterns += patterns(
    '',
    url(r'^$', DevHomepageSelector.as_view(), name='dev-homepage'),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Redirect to our favicon,ico file, which is empty. This supresses the 'Not
# Found: /favicon.ico' log output which would otherwise appear during the
# selenium testing.
urlpatterns += patterns('',
    (r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL+'favicon.ico')),
)
