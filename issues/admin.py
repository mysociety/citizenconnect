from django.contrib import admin

import reversion

from .models import Problem, Question

class ProblemAdmin(reversion.VersionAdmin):
        pass
admin.site.register(Problem, ProblemAdmin)

class QuestionAdmin(reversion.VersionAdmin):
        pass
admin.site.register(Question, QuestionAdmin)