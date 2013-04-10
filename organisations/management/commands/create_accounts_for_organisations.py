import logging
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand, CommandError

from ...models import Organisation

class Command(BaseCommand):
    help = 'Create accounts for organisations that don\'t have one yet'

    def handle(self, *args, **options):
        orgs_without_accounts = Organisation.objects.all().filter(users=None)

        logger.info('{0} Organisations to create accounts for'.format(len(orgs_without_accounts)))

        for organisation in orgs_without_accounts:
            if not organisation.email: # ISSUE-329
                logger.warn('Skipping {0} ({1}) as it has no email'.format(organisation.name, organisation.id))
            else:
                organisation.ensure_related_user_exists()


