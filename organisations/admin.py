from django.contrib import admin
from organisations import models

import reversion


class SiteAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'organisation_type', 'trust')


class SiteParentAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')


class RegulatorAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')


class ServiceAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'service_code', 'organisation')


admin.site.register(models.Site, SiteAdmin)
admin.site.register(models.SiteParent, SiteParentAdmin)
admin.site.register(models.Regulator, RegulatorAdmin)
admin.site.register(models.Service, ServiceAdmin)
