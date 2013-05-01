import requests
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count

from organisations.models import Organisation


class Command(BaseCommand):
    help = 'Push new reviews to the Choices API'

    def handle(self, *args, **options):
        organisations = Organisation.objects.annotate(num_reviews=Count('review')).filter(num_reviews__gt=0)

        for organisation in organisations:
            self.stdout.write("Posting {0} reviews to {1}\n".format(organisation.review_set.count(), self.choices_api_url(organisation.ods_code)))
            response = requests.post(self.choices_api_url(organisation.ods_code), data=self.xml_encoded_reviews(organisation.review_set.all()), headers={'content-type': 'application/xml'})
            self.stdout.write("Response status code: {0}\n".format(response.status_code))

    def choices_api_url(self, ods_code):
        return "{0}comments/{1}?apikey={2}".format(settings.NHS_CHOICES_BASE_URL, ods_code, settings.NHS_CHOICES_API_KEY)

    def xml_encoded_reviews(self, reviews):
        return render_to_string('reviews/choices_review.xml', {
            'reviews': reviews,
            'posting_organisation_id': settings.NHS_CHOICES_POSTING_ORGANISATION_ID
        })
