from urlparse import urlparse

from django.core.management.base import NoArgsCommand
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
        if settings.SITE_BASE_URL:
            base_domain = urlparse(settings.SITE_BASE_URL).netloc
            if not base_domain:
                raise ValueError("settings.SITE_BASE_URL is not a valid fully qualified domain.")
            try:
                default_site = Site.objects.get(id=1)
                default_site.domain = base_domain
                default_site.save()
            except Site.DoesNotExist:
                Site.objects.create(name="Default Site", domain=base_domain)
