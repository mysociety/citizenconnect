from django.http import HttpResponse
from django.template import Context, loader

from .exceptions import LoginBlockedError


class FailedLoginBlockerMiddleware(object):
    def process_exception(self, request, exception):
        if type(exception) is not LoginBlockedError:
            return

        template = loader.get_template('failedloginblocker/blocked.html')
        context = Context({
            'exception': exception,
        })
        response = HttpResponse(template.render(context))
        response.status_code = 403
        return response
