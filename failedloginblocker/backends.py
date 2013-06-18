from django.contrib.auth.backends import ModelBackend

from .decorators import monitor_login


class MonitoredModelBackend(ModelBackend):

    @monitor_login
    def authenticate(self, **credentials):
        super(MonitoredModelBackend, self).authenticate(**credentials)
