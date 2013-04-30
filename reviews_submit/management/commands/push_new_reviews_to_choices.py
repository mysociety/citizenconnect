import requests
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings

from ...models import Review


class Command(BaseCommand):
    help = 'Push new reviews to the Choices API'

    def handle(self, *args, **options):
        reviews = Review.objects.all()
        xml_string = render_to_string('reviews/choices_review.xml', {
            'reviews': reviews,
            'posting_organisation_id': settings.NHS_CHOICES_POSTING_ORGANISATION_ID
        })

        response = requests.post(self.choices_api_url(), data=xml_string, headers={'content-type': 'application/xml'})

        print("Response status: %s" % response.status_code)

    def choices_api_url(self):
        return "{0}?apikey={1}".format(settings.NHS_CHOICES_BASE_URL, settings.NHS_CHOICES_API_KEY)
