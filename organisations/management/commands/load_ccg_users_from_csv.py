from django.core.management.base import BaseCommand, CommandError

from ...models import CCG
from ..load_users import from_csv


class Command(BaseCommand):
    args = '<csv_file>'
    help = "Create user accounts for CCGs from a csv"

    def handle(self, *args, **options):
        if len(args) is 0:
            raise CommandError("Please supply a csv file to import from")

        from_csv(filename=args[0], org_parent_or_ccg_model=CCG)
