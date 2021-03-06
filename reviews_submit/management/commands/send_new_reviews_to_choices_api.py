import requests

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import Count
from django.utils import timezone

from organisations.models import Organisation
from organisations.choices_api import ChoicesAPI


class Command(BaseCommand):
    help = 'Push new reviews to the Choices API'

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        organisations = Organisation.objects.annotate(num_reviews=Count('submitted_reviews')).filter(num_reviews__gt=0)

        for organisation in organisations:
            url = self.choices_api_url(organisation)
            reviews = organisation.submitted_reviews.filter(last_sent_to_api__isnull=True)
            if not reviews:
                if verbosity >= 1:
                    self.stdout.write("No reviews found for {0}\n".format(organisation))
                continue

            for review in reviews:
                data = self.xml_encode(review)
                response = requests.post(url, data=data, headers={'content-type': 'application/xml'})

                if response.status_code == 202:
                    if verbosity >= 1:
                        self.stdout.write("{0}: Sent review to the Choices API\n".format(review.id))
                    review.last_sent_to_api = timezone.now()
                    review.save()

                elif response.status_code == 400:
                    if verbosity >= 1:
                        self.stderr.write("{0}: The XML has invalid fields\n".format(review.id))

                elif response.status_code == 401:
                    if verbosity >= 1:
                        self.stderr.write("{0}: The API key does not have permission\n".format(review.id))

                elif response.status_code == 403:
                    if verbosity >= 1:
                        self.stderr.write("{0}: PostingID is a duplicate\n".format(review.id))

                elif response.status_code == 404:
                    if verbosity >= 1:
                        self.stderr.write("{0}: The NACS code {1} is not valid\n".format(review.id, review.organisation.ods_code))

                elif response.status_code == 500:
                    if verbosity >= 1:
                        self.stderr.write("{0}: Server error\n".format(review.id, review.organisation.ods_code))

    def choices_api_url(self, organisation):
        """Return the choices api url for submitting a review about a specific organisation."""
        # If the org is a gp, use its' parent's ods_code, because the Choices
        # api doesn't know about gp branches (what we have) - only gp surgeries
        # as a whole.
        if organisation.organisation_type == "gppractices":
            ods_code = organisation.parent.code
        else:
            ods_code = organisation.ods_code
        return ChoicesAPI().construct_url(['comment', ods_code])

    def xml_encode(self, review):
        return render_to_string('reviews/choices_review.xml', {
            'review': review,
            'posting_organisation_id': settings.NHS_CHOICES_POSTING_ORGANISATION_ID
        }).encode('utf8')
