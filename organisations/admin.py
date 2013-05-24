from django.contrib import admin
from organisations import models

import reversion

class OrganisationAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'organisation_type', 'county', 'postcode', 'email')

class CCGAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')

admin.site.register(models.Organisation, OrganisationAdmin)
admin.site.register(models.CCG, CCGAdmin)
