from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Admin section
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'citizenconnect.views.home', name='home'),
    url(r'^ask-question$', 'citizenconnect.views.ask_question', name='ask-question'),
    url(r'^pick-provider$', 'citizenconnect.views.pick_provider', name='pick-provider'),
    url(r'^provider-results$', 'citizenconnect.views.provider_results', name='provider-results'),
    url(r'^question-form$', 'citizenconnect.views.question_form', name='question-form'),
    url(r'^question-confirm$', 'citizenconnect.views.question_confirm', name='question-confirm'),
    # url(r'^citizenconnect/', include('citizenconnect.foo.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

