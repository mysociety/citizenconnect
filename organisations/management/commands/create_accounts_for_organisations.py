import logging
from exceptions import AttributeError

from django.core import mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django.contrib.auth.models import Group

from ...models import Organisation
import organisations.auth as auth
from ...auth import create_unique_username

logger = logging.getLogger(__name__)

@transaction.commit_manually
class Command(BaseCommand):
    help = 'Create accounts for organisations that don\'t have one yet'

    def handle(self, *args, **options):
        orgs_without_accounts = Organisation.objects.all().filter(users=None)
        providers_group = Group.objects.get(pk=auth.PROVIDERS)

        logger.info('{0} Organisations to create accounts for'.format(len(orgs_without_accounts)))

        for organisation in orgs_without_accounts:
            logger.info('Creating account for {0} (ODS code: {1})'.format(organisation.name,
                                                                           organisation.ods_code))
            try:
                new_account = User.objects.create_user(create_unique_username(organisation),
                                                       organisation.email)
                new_account.groups.add(providers_group)
                new_account.save()

                organisation.users.add(new_account)
                organisation.save()

                transaction.commit()
            except Exception as e:
                logger.error('{0}'.format(e))
                logger.error('Error creating account for {0} (ODS code: {1})'.format(organisation.name,
                                                                                     organisation.ods_code))
                transaction.rollback()



