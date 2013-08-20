import csv
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand

from ...models import OrganisationParent, CCG


class Command(BaseCommand):
    args = '<csv_file>'
    help = 'Load Organisation Parents from a spreadsheet extracted from the NHS Choices database'

    option_list = BaseCommand.option_list + (
        make_option(
            '--update',
            action='store_true',
            dest='update',
            default=False,
            help='Update existing organisation parent attributes'),
    )
        # + (
        # make_option('--clean',
        #     action='store_true',
        #     dest='clean',
        #     default=False,
        #     help='Delete existing organisation parents'),
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
        verbosity = int(options.get('verbosity'))
        # clean = options['clean']
        update = options['update']

        # if clean:
        #     if verbosity >= 2:
        #         self.stdout.write("Deleting existing organisation parents")
        #     Service.objects.all().delete()
        #     OrganisationParent.objects.all().delete()

        if verbosity >= 2:
            processed = 0
            skipped = 0

        for row in reader:
            rownum += 1

            for key, val in row.items():
                row[key] = self.clean_value(val)

            try:
                # Remember to update the docs in documentation/csv_formats.md if you make changes here
                ods_code = self.clean_value(row['ODS Code'])
                choices_id = self.clean_value(row['Choices ID'])
                name = self.clean_value(row['Name'])
                email = self.clean_value(row['Email'])
                secondary_email = self.clean_value(row['Secondary Email'])
                primary_ccg_code = self.clean_value(row['Primary CCG'])
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
                primary_ccg = CCG.objects.get(code=primary_ccg_code)
            except CCG.DoesNotExist:
                raise Exception(
                    "Could not find 'Primary CCG' with code '{0}' on line {1}".format(
                        primary_ccg_code, rownum
                    )
                )
            finally:
                transaction.rollback()

            all_ccgs = set()
            all_ccgs.add(primary_ccg)
            for other_code in other_ccg_codes:
                if other_code == '':
                    continue
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

            org_parent_defaults = {
                'choices_id': choices_id,
                'name': name,
                'email': email,
                'secondary_email': secondary_email,
                'primary_ccg': primary_ccg,
            }

            try:
                org_parent, org_parent_created = OrganisationParent.objects.get_or_create(
                    code=ods_code,
                    defaults=org_parent_defaults
                )

                if update:
                    OrganisationParent.objects.filter(id=org_parent.id).update(**org_parent_defaults)

                if org_parent_created or update:
                    # Delete all current CCG links and set the one we expect
                    org_parent.ccgs.clear()
                    for ccg in all_ccgs:
                        org_parent.ccgs.add(ccg)

                if org_parent_created:
                    self.stdout.write('Created organisation parent %s\n' % org_parent.name)
                elif verbosity >= 2:
                    self.stdout.write('Organisation Parent %s exists\n' % ods_code)
                if verbosity >= 2:
                    processed += 1
                transaction.commit()
            except Exception as e:
                if verbosity >= 2:
                    skipped += 1
                self.stderr.write("Skipping %s (%s): %s" % (name, ods_code, e))
                transaction.rollback()

        if verbosity >= 2:
            self.stdout.write("Total records in file: {0}\n".format(rownum))
            self.stdout.write("Processed {0} records\n".format(processed))
            self.stdout.write("Skipped {0} records\n".format(skipped))
