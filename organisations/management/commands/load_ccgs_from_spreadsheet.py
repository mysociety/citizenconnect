import csv
from optparse import make_option

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError

from ...models import CCG

class Command(BaseCommand):
    help = 'Load CCGs from a spreadsheet'

    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose output'),
        )

    @transaction.commit_manually
    def handle(self, *args, **options):
        filename = args[0]
        allowed_regions = ['London']
        reader = csv.DictReader(open(filename), delimiter=',', quotechar='"')
        rownum = 0
        verbose = options['verbose']

        if verbose:
            processed = 0
            skipped = 0

        for row in reader:
            rownum += 1

            try:
                code = row['Code']
                name = row['Name']
                region = row['Region']
                email = row['Email']
            except KeyError as message:
                raise Exception("Missing column with the heading '{0}'".format(message))

            if region not in allowed_regions:
                if verbose:
                    self.stdout.write("Skipping %s - not in allowed regions\n" % name)
                    skipped += 1
                continue

            ccg_defaults = {'name': name, 'email': email}

            try:
                ccg, ccg_created = CCG.objects.get_or_create(code=code,
                                                             defaults=ccg_defaults)
                if ccg_created:
                    self.stdout.write('Created CCG %s\n' % ccg.name)
                if verbose:
                    processed += 1
                transaction.commit()

            except Exception as e:
                if verbose:
                    skipped += 1
                self.stderr.write("Skipping %s %s: %s" % (name, code, e))
                transaction.rollback()


        if verbose:
            # First row is a header, so ignore it in the count
            self.stdout.write("Total records in file: {0}\n".format(rownum-1))
            self.stdout.write("Processed {0} records\n".format(processed))
            self.stdout.write("Skipped {0} records\n".format(skipped))

