from urlparse import urlparse

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from django.contrib.sites.models import Site


class Command(NoArgsCommand):
    """
    This command creates or updates the first entry in the sites
    database, with the domain set to the domain part of
    settings.SITE_BASE_URL
    """

    help = "Create or update site id 1 with the domain in settings.SITE_BASE_URL"

    def handle_noargs(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        if settings.SITE_BASE_URL:
            if verbosity >= 2:
                self.stdout.write("settings.SITE_BASE_URL = %s\n" % settings.SITE_BASE_URL)
            base_domain = urlparse(settings.SITE_BASE_URL).netloc
            if not base_domain:
                raise CommandError("settings.SITE_BASE_URL is not a valid fully qualified domain.")
            try:
                default_site = Site.objects.get(id=1)
                default_site.domain = base_domain
                default_site.save()
                if verbosity >= 1:
                    self.stdout.write("Updated Site id=1\n")
            except Site.DoesNotExist:
                Site.objects.create(name="Default Site", domain=base_domain)
                if verbosity >= 1:
                    self.stdout.write("Created Site id=1\n")
        else:
            raise CommandError("settings.SITE_BASE_URL has not been set")
