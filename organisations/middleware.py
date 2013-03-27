import auth
from .auth import user_in_group
from .models import SuperuserLogEntry, Organisation

class SuperuserLogEntryMiddleware(object):
    def process_response(self, request, response):
        # Log accesses to pages by NHS Superusers
        if getattr(request, 'user', False):
            if user_in_group(request.user, auth.NHS_SUPERUSERS):
                log_entry = SuperuserLogEntry(user=request.user, path=request.path)
                log_entry.save()
        return response
