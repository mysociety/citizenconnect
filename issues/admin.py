from sorl.thumbnail import get_thumbnail
from sorl.thumbnail.admin import AdminImageMixin

from django.contrib import admin

import reversion

from .models import Problem, ProblemImage

class ProblemImageAdmin(AdminImageMixin, reversion.VersionAdmin):
    list_display = [ 'thumbnail', 'problem' ]
    
    def thumbnail(self, obj):
        im = get_thumbnail(obj.image, '100x100')
        return '<img src="%s" />' % ( im.url )
    thumbnail.allow_tags = True


class ProblemImageAdminInline(AdminImageMixin, admin.TabularInline):
    model        = ProblemImage


class ProblemAdmin(reversion.VersionAdmin):
    list_display = ('reference_number', 'public', 'status', 'organisation')
    inlines = [ProblemImageAdminInline]


admin.site.register(ProblemImage, ProblemImageAdmin)
admin.site.register(Problem, ProblemAdmin)
