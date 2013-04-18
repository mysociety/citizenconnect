import logging
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand, CommandError

from ...models import Organisation, CCG

class Command(BaseCommand):
    help = 'Create accounts for organisations that don\'t have one yet'

    def handle(self, *args, **options):

        for model in [Organisation, CCG]:
            objs_without_accounts = model.objects.all().filter(users=None)
            
            logger.info('{0} {1} to create accounts for'.format(objs_without_accounts.count(), model.__name__))
            
            for obj in objs_without_accounts:
                if not obj.email: # ISSUE-329
                    logger.warn('Skipping {0} ({1}) as it has no email'.format(obj.name, obj.id))
                else:
                    obj.ensure_related_user_exists()


