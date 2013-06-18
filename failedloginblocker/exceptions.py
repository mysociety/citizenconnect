from django.conf import settings

class LoginBlockedError(Exception):
    def __init__(self):
        msg = "Your account has been locked due to too many failed login attempts."
        msg += " Contact us to have your account reactivated."
        msg += " Alternatively wait {0} minutes then try again.".format(settings.FLB_BLOCK_INTERVAL)
        super(LoginBlockedError, self).__init__(msg)
