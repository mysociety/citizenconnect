from django.http import HttpResponse
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.decorators import decorator_from_middleware


class BasicAuthMiddleware(object):

    def unauthed(self):
        response = HttpResponse('Error: Authentication required', mimetype="text/plain")
        response['WWW-Authenticate'] = 'Basic realm="NHSD API"'
        response.status_code = 401
        return response

    def process_request(self, request):
        if not 'HTTP_AUTHORIZATION' in request.META:

            return self.unauthed()
        else:
            authentication = request.META['HTTP_AUTHORIZATION']
            (authmeth, auth) = authentication.split(' ', 1)
            if 'basic' != authmeth.lower():
                return self.unauthed()
            auth = auth.strip().decode('base64')
            username, password = auth.split(':', 1)
            if username == settings.API_BASICAUTH_USERNAME and password == settings.API_BASICAUTH_PASSWORD:
                return None

            return self.unauthed()


basic_auth = decorator_from_middleware(BasicAuthMiddleware)
