from django.contrib import admin

import reversion

from .models import Problem

class ProblemAdmin(reversion.VersionAdmin):
        pass
admin.site.register(Problem, ProblemAdmin)
