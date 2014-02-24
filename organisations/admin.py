from sorl.thumbnail.admin import AdminImageMixin

from django.contrib import admin
from django.conf.urls import patterns, url
from django.shortcuts import render_to_response
from django.template import RequestContext

from . import models
from .forms import SurveyAdminCSVUploadForm


import reversion


class OrganisationAdmin(AdminImageMixin, reversion.VersionAdmin):
    list_display = ('id', 'name', 'organisation_type', 'parent')


class OrganisationParentAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')


class CCGAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'code', 'email')


class ServiceAdmin(reversion.VersionAdmin):
    list_display = ('id', 'name', 'service_code', 'organisation')


class FriendsAndFamilySurveyAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'location', 'date')

    def get_urls(self):
        urls = super(FriendsAndFamilySurveyAdmin, self).get_urls()
        my_urls = patterns(
            '',
            url(
                r'^upload_csv/$',
                self.admin_site.admin_view(self.upload_csv),
                name="organisations_friendsandfamilysurvey_survey_upload_csv"
            )
        )
        return my_urls + urls

    def upload_csv(self, request):
        """Custom Admin view which presents a form for uploading CSV files of
        surveys for bulk uploading"""

        if request.method == 'POST':
            form = SurveyAdminCSVUploadForm(request.POST, request.FILES)
        else:
            form = SurveyAdminCSVUploadForm()

        # We copy the Django admins' Change Form's template for some bits,
        # like breadcrumbs, so I build the context for the template in a
        # similar way too.
        context = RequestContext(
            request,
            current_app=self.admin_site.name,
        )
        context.update({
            'title': 'Upload Survey CSV',
            'has_change_permission': self.has_change_permission(request),
            'opts': self.model._meta
        })

        if form.is_valid():
            # note - for this to work the TemporaryFileUploadHandler upload
            # handler needs to be the default
            csv_file = form.cleaned_data.get('csv_file')
            survey_context = form.cleaned_data.get('context')
            location = form.cleaned_data.get('location')
            date = form.cleaned_data.get('month')
            try:
                context['created'], context['skipped'] = models.FriendsAndFamilySurvey.process_csv(csv_file, date, survey_context, location)
            except Exception as e:
                # Something went wrong processing it, probably duff data:
                context['csv_processing_error'] = e.message

        return render_to_response(
            'organisations/admin/survey_upload_csv.html',
            {
                'form': form,
            },
            context_instance=context,
        )

admin.site.register(models.Organisation, OrganisationAdmin)
admin.site.register(models.OrganisationParent, OrganisationParentAdmin)
admin.site.register(models.CCG, CCGAdmin)
admin.site.register(models.Service, ServiceAdmin)
admin.site.register(models.FriendsAndFamilySurvey, FriendsAndFamilySurveyAdmin)
