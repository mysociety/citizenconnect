from django.contrib import admin
from organisations import models

import reversion

class OrganisationAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'organisation_type', 'trust')

class TrustAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')

class CCGAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')

class ServiceAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'service_code', 'organisation')


admin.site.register(models.Organisation, OrganisationAdmin)
admin.site.register(models.Trust, TrustAdmin)
admin.site.register(models.CCG, CCGAdmin)
admin.site.register(models.Service, ServiceAdmin)
