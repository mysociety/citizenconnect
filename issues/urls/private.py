from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import login_required

from ..views import *

urlpatterns = patterns('',
    url(r'^question/update/(?P<pk>\d+)$', login_required(QuestionUpdate.as_view()), name='question-update'),
)
