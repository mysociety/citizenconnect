from django.contrib import admin
from organisations import models

import reversion

class OrganisationAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'organisation_type', 'county', 'postcode')

admin.site.register(models.Organisation, OrganisationAdmin)
