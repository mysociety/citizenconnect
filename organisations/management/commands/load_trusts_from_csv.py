import csv
from optparse import make_option

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from ...models import Trust, Service, CCG


class Command(BaseCommand):
    help = 'Load trusts from a spreadsheet extracted from the NHS Choices database'

    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose output'),
        ) + (
        make_option('--update',
            action='store_true',
            dest='update',
            default=False,
            help='Update existing trust and service attributes'),
        )
        # + (
        # make_option('--clean',
        #     action='store_true',
        #     dest='clean',
        #     default=False,
        #     help='Delete existing trusts, and associated organisations etc'),
        # )


    def clean_value(self, value):
        if value == 'NULL':
            return ''
        else:
            return value

    @transaction.commit_manually
    def handle(self, *args, **options):
        filename = args[0]
        reader = csv.DictReader(open(filename), delimiter=',', quotechar='"')
        rownum = 0
        verbose = options['verbose']
        # clean = options['clean']
        update = options['update']

        # if clean:
        #     if verbose:
        #         self.stdout.write("Deleting existing trusts and services")
        #     Service.objects.all().delete()
        #     Trust.objects.all().delete()

        if verbose:
            processed = 0
            skipped = 0

        for row in reader:
            rownum += 1

            for key, val in row.items():
                row[key] = self.clean_value(val)

            try:
                # Remember to update the docs in documentation/csv_formats.md if you make changes here
                ods_code = self.clean_value(row['ODS Code'])
                name     = self.clean_value(row['Name']    )
                email    = self.clean_value(row['Email']   )
                secondary_email = self.clean_value(row['Secondary Email'])
                escalation_ccg_code = self.clean_value(row['Escalation CCG'] )
                other_ccg_codes = self.clean_value(row['Other CCGs'] or '').split(r'|')

            except KeyError as message:
                raise Exception("Missing column with the heading '{0}'".format(message))
            finally:
                transaction.rollback()

            # Skip blank lines
            if not ods_code:
                continue

            # load the various CCGs
            try:
                escalation_ccg = CCG.objects.get(code=escalation_ccg_code)
            except CCG.DoesNotExist:
                raise Exception(
                    "Could not find 'Escalation CCG' with code '{0}' on line {1}".format(
                        escalation_ccg_code, rownum
                    )
                )
            finally:
                transaction.rollback()

            all_ccgs = set()
            all_ccgs.add(escalation_ccg)
            for other_code in other_ccg_codes:
                if other_code == '': continue
                try:
                    all_ccgs.add(CCG.objects.get(code=other_code))
                except CCG.DoesNotExist:
                    raise Exception(
                        "Could not find 'Other CCGs' entry with code '{0}' on line {1}".format(
                            other_code, rownum
                        )
                    )
                finally:
                    transaction.rollback()

            trust_defaults = {
                'name': name,
                'email': email,
                'secondary_email': secondary_email,
                'escalation_ccg': escalation_ccg,
            }

            try:
                trust, trust_created = Trust.objects.get_or_create(
                    code=ods_code,
                    defaults=trust_defaults
                )

                if update:
                    Trust.objects.filter(id=trust.id).update(**trust_defaults)

                if trust_created or update:
                    # Delete all current CCG links and set the one we expect
                    trust.ccgs.clear()
                    for ccg in all_ccgs:
                        trust.ccgs.add(ccg)

                if trust_created:
                    self.stdout.write('Created trust %s\n' % trust.name)
                elif verbose:
                    self.stdout.write('Trust %s exists\n' % ods_code)
                if verbose:
                    processed += 1
                transaction.commit()
            except Exception as e:
                if verbose:
                    skipped += 1
                self.stderr.write("Skipping %s (%s): %s" % (name, ods_code, e))
                transaction.rollback()

        if verbose:
            self.stdout.write("Total records in file: {0}\n".format(rownum))
            self.stdout.write("Processed {0} records\n".format(processed))
            self.stdout.write("Skipped {0} records\n".format(skipped))
