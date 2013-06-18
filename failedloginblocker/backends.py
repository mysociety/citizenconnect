from django.contrib.auth.backends import ModelBackend

from .decorators import monitor_login


class MonitoredModelBackend(ModelBackend):
    """
    Custom auth backend which monitors login attempts and blocks after
    a preconfigured number of failures.
    """

    @monitor_login
    def authenticate(self, **credentials):
        return super(MonitoredModelBackend, self).authenticate(**credentials)
