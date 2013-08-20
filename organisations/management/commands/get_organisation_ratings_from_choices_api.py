from django.core.management.base import BaseCommand
from django.db import transaction

from ...choices_api import ChoicesAPI
from ...models import Organisation


class Command(BaseCommand):
    help = 'Load organisations from the Choices API'

    @transaction.commit_manually
    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))

        api = ChoicesAPI()
        for organisation in Organisation.objects.all():
            try:
                rating = api.get_organisation_recommendation_rating(organisation_type=organisation.organisation_type,
                                                                    choices_id=organisation.choices_id)
                if rating is not None:
                    organisation.average_recommendation_rating = rating
                    organisation.save()

                    if verbosity >= 1:
                        self.stdout.write('Updated rating for organisation %s\n' % organisation.name)
                    transaction.commit()
            except Exception as e:
                if verbosity >= 1:
                    self.stderr.write("Error updating rating for %s\n" % (organisation.name))
                    self.stderr.write(str(e))
                transaction.rollback()
