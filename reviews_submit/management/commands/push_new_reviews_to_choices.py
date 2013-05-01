import requests

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from organisations.models import Organisation


class Command(BaseCommand):
    help = 'Push new reviews to the Choices API'

    def handle(self, *args, **options):
        organisations = Organisation.objects.annotate(num_reviews=Count('review')).filter(num_reviews__gt=0)

        for organisation in organisations:
            reviews = organisation.review_set.filter(last_sent_to_api__isnull=True)
            url = self.choices_api_url(organisation.ods_code)
            data = self.xml_encoded_reviews(reviews)

            response = requests.post(url, data=data, headers={'content-type': 'application/xml'})

            if response.status_code == 202:
                self.stdout.write("{0}: Sent {1} review to the Choices API\n".format(response.status_code, reviews.count()))
                reviews.update(last_sent_to_api=timezone.now())
                return

            if response.status_code == 400:
                self.stderr.write("{0}: The XML has invalid fields\n".format(response.status_code))
                return

    def choices_api_url(self, ods_code):
        return "{0}comment/{1}?apikey={2}".format(
            settings.NHS_CHOICES_BASE_URL, ods_code,
            settings.NHS_CHOICES_API_KEY)

    def xml_encoded_reviews(self, reviews):
        return render_to_string('reviews/choices_review.xml', {
            'reviews': reviews,
            'posting_organisation_id': settings.NHS_CHOICES_POSTING_ORGANISATION_ID
        })
