from django.contrib import admin

import reversion

from .models import Problem

class ProblemAdmin(reversion.VersionAdmin):
    list_display = ('reference_number', 'public', 'status', 'organisation')

admin.site.register(Problem, ProblemAdmin)
