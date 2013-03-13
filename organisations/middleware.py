from .models import SuperuserLogEntry, Organisation

class SuperuserLogEntryMiddleware(object):
    def process_response(self, request, response):
        # Log accesses to pages by NHS Superusers
        if getattr(request, 'user', False):
            if request.user.groups.filter(pk=Organisation.NHS_SUPERUSERS).exists():
                log_entry = SuperuserLogEntry(user=request.user, path=request.path)
                log_entry.save()
        return response
