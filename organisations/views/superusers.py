import csv
from datetime import datetime, timedelta

# Django imports
from django.views.generic import View, TemplateView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone
from django.template.defaultfilters import pluralize

from issues.models import Problem

from ..auth import user_is_superuser
from ..models import SuperuserLogEntry, CCG, OrganisationParent


class SuperuserOnlyMixin(object):

    def dispatch(self, request, *args, **kwargs):
        if not user_is_superuser(request.user):
            raise PermissionDenied()
        return super(SuperuserOnlyMixin, self).dispatch(request, *args, **kwargs)


class SuperuserDashboard(SuperuserOnlyMixin, TemplateView):
    template_name = 'organisations/superuser_dashboard.html'

    def get_context_data(self, **kwargs):

        context = super(SuperuserDashboard, self).get_context_data(**kwargs)
        context['ccgs'] = CCG.objects.all()
        context['organisation_parents'] = OrganisationParent.objects.all()

        return context


class SuperuserLogs(SuperuserOnlyMixin, TemplateView):

    template_name = 'organisations/superuser_logs.html'

    def get_context_data(self, **kwargs):
        context = super(SuperuserLogs, self).get_context_data(**kwargs)
        context['logs'] = SuperuserLogEntry.objects.all()
        return context


class ProblemsCSV(SuperuserOnlyMixin, View):

    def minutes_as_days_hours_mins(self, minutes):
        """Format a number of minutes as days, hours, minutes, only showing
        the values we need to.

        Taken from: http://stackoverflow.com/questions/4048651/python-function-to-convert-seconds-into-minutes-hours-and-days
        with some adjustments."""
        if minutes is None:
            return ""
        td = timedelta(minutes=minutes)
        d = datetime(1,1,1) + td
        if d.day-1 > 0:
            return "%d day%s, %d hour%s, %d minute%s" % (d.day-1, pluralize(d.day-1), d.hour, pluralize(d.hour), d.minute, pluralize(d.minute))
        elif d.hour > 0:
            return "%d hour%s, %d minute%s" % (d.hour, pluralize(d.hour), d.minute, pluralize(d.minute))
        else:
            return "%d minute%s" % (d.minute, pluralize(d.minute))

    def get(self, request, *args, **kwargs):
        """Custom Admin view which allows the user to download a CSV of all
        the problems in the database."""

        date_format = '%d/%m/%Y %H:%M'

        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        filename = 'careconnect-problems-{0}.csv'.format(timezone.now().strftime('%d-%m-%Y'))
        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)

        # Define the field names
        field_names = [
            'ID',
            'Organisation',
            'Service',
            'Created',
            'Status',
            'Privacy', # Public and Public Reporter name in one field
            'Category',
            'Original Description',
            'Moderated Description',
            'Reporter Name',
            'Reporter Email',
            'Reporter Phone',
            'Preferred Contact Method',
            'Source',
            'Website', # cobrand in the model
            'Published', # publication_status in the model
            'Priority',
            'Under 16',
            'Breach',
            'Commissioned',
            'Formal Complaint',
            'Time to Acknowledge',
            'Time to Address',
            'Last Modified',
            'Resolved',
            'Survey Sent',
            'Happy with Service',
            'Happy with Outcome',
        ]

        # Make a csv writer
        writer = csv.DictWriter(response, field_names)

        # Write out a heading row
        # Note: If we only had to support Python 2.7 we could use:
        # http://docs.python.org/2/library/csv.html#csv.DictWriter.writeheader
        writer.writerow(dict([(f,f) for f in field_names]))

        # Write out the problems
        for problem in Problem.objects.all().order_by("created"):
            if not problem.public:
                problem_privacy = "Private"
            else:
                if problem.public_reporter_name:
                    problem_privacy = "Public with reporter name"
                else:
                    problem_privacy = "Public, anonymous"

            problem_row = {
                'ID': problem.id,
                'Organisation': problem.organisation.name,
                'Service': problem.service.name if problem.service else "",
                'Created': problem.created.strftime(date_format),
                'Status': problem.get_status_display(),
                'Privacy': problem_privacy,
                'Category': problem.get_category_display(),
                'Original Description': problem.description,
                'Moderated Description': problem.moderated_description,
                'Reporter Name': problem.reporter_name,
                'Reporter Email': problem.reporter_email,
                'Reporter Phone': problem.reporter_phone,
                'Preferred Contact Method': problem.preferred_contact_method,
                'Source': problem.source,
                'Website': problem.cobrand,
                'Published': problem.get_publication_status_display(),
                'Priority': "High" if (problem.priority == 50) else 'Normal',
                'Under 16': str(problem.reporter_under_16),
                'Breach': str(problem.breach),
                'Commissioned': problem.get_commissioned_display(),
                'Formal Complaint': str(problem.formal_complaint),
                'Time to Acknowledge': self.minutes_as_days_hours_mins(problem.time_to_acknowledge),
                'Time to Address': self.minutes_as_days_hours_mins(problem.time_to_address),
                'Last Modified': problem.modified.strftime(date_format) if problem.modified else "",
                'Resolved': problem.resolved.strftime(date_format) if problem.resolved else "",
                'Survey Sent': problem.survey_sent.strftime(date_format) if problem.survey_sent else "",
                'Happy with Service': problem.happy_service,
                'Happy with Outcome': problem.happy_outcome,
            }
            writer.writerow(problem_row)

        return response
