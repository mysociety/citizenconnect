from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from .views import Home, CobrandChoice, About
# Admin section
from django.contrib import admin
admin.autodiscover()


allowed_cobrands = settings.ALLOWED_COBRANDS
cobrand_pattern = '(?P<cobrand>%s)' % '|'.join(allowed_cobrands)
urlpatterns = patterns('',
    # Examples:
    url(r'^$', CobrandChoice.as_view(), name='cobrand-choice'),
    url(r'^' + cobrand_pattern + r'/?$', Home.as_view(), name='home'),
    url(r'^' + cobrand_pattern + r'/about$', About.as_view(), name='about'),

    url(r'^' + cobrand_pattern + r'/question/', include('questions.urls')),
    url(r'^' + cobrand_pattern + r'/problem/', include('problems.urls')),
    url(r'^' + cobrand_pattern + r'/review/', include('reviews.urls')),
    url(r'^' + cobrand_pattern + r'/stats/', include('organisations.urls.public')),
    url(r'^' + cobrand_pattern + r'/moderate/', include('moderation.urls')),

    # private is the namespace for NHS-staff only pages
    url(r'^private/', include('organisations.urls.private')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

