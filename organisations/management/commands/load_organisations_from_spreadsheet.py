import csv
from optparse import make_option

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from ...models import Organisation, Service, CCG


class Command(BaseCommand):
    help = 'Load organisations from a spreadsheet extracted from the NHS Choices database'

    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose output'),
        ) + (
        make_option('--clean',
            action='store_true',
            dest='clean',
            default=False,
            help='Delete existing organisations and services, and associated problems'),
        ) + (
        make_option('--update',
            action='store_true',
            dest='update',
            default=False,
            help='Update existing organisation and service attributes'),
        )

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
        clean = options['clean']
        update = options['update']

        if clean:
            if verbose:
                self.stdout.write("Deleting existing organisations and services")
            Service.objects.all().delete()
            Organisation.objects.all().delete()

        if verbose:
            processed = 0
            skipped = 0

        type_mappings = {'HOS': 'hospitals',
                         'GPB': 'gppractices'}

        for row in reader:
            rownum += 1

            for key, val in row.items():
                row[key] = self.clean_value(val)

            try:
                choices_id = row['ChoicesID']
                ods_code = row['OrganisationCode']
                name = row['OrganisationName']
                organisation_type_text = row['OrganisationTypeID']
                last_updated = row['LastUpdatedDate']

                trust = row['TrustName']
                organisation_contact = row['OrganisationContact']

                url = row['URL']

                address_line1 = row['Address1']
                address_line2 = row['Address2']
                address_line3 = row['Address3']
                city = row['City']
                county = row['County']
                postcode = row['Postcode']

                lat = row['Latitude']
                lon = row['Longitude']

                service_code = row['ServiceCode']
                service_name = row['ServiceName']

                escalation_ccg_code = row['CCGCode']

            except KeyError as message:
                raise Exception("Missing column with the heading '{0}'".format(message))
            finally:
                transaction.rollback()

            # Skip blank lines
            if not choices_id:
                continue

            # load the CCG
            try:
                escalation_ccg = CCG.objects.get(code=escalation_ccg_code)
            except CCG.DoesNotExist:
                raise Exception(
                    "Could not find CCG with code '{0}' on line {1}".format(
                        escalation_ccg_code, rownum
                    )
                )
            finally:
                transaction.rollback()

            if organisation_type_text not in type_mappings:
                if verbose:
                    print "Unknown organisation type %s, skipping" % organisation_type_text
                continue
            organisation_type = type_mappings[organisation_type_text]
            organisation_defaults = {'choices_id': choices_id,
                                     'name': name,
                                     'organisation_type': organisation_type,
                                     'point': Point(float(lon), float(lat)),
                                     'address_line1': address_line1,
                                     'address_line2': address_line2,
                                     'address_line3': address_line3,
                                     'city': city,
                                     'county': county,
                                     'postcode': postcode,
                                     'email': organisation_contact,
                                     'escalation_ccg': escalation_ccg}
            try:
                organisation, organisation_created = Organisation.objects.get_or_create(ods_code=ods_code,
                                                                                        defaults=organisation_defaults)
                if update:
                    Organisation.objects.filter(id=organisation.id).update(**organisation_defaults)
                service = None
                # Only hospitals have services
                if organisation_type == 'hospitals':
                    if service_name and service_name != 'NULL':
                        service_defaults = {'name': service_name}
                        service, service_created = Service.objects.get_or_create(organisation=organisation,
                                                                                 service_code=service_code,
                                                                                 defaults=service_defaults)

                        if update:
                            Service.objects.filter(id=service.id).update(**service_defaults)
                if organisation_created:
                    self.stdout.write('Created organisation %s\n' % organisation.name)
                elif verbose:
                    self.stdout.write('Organisation %s exists\n' % ods_code)
                if service:
                    if service_created:
                        self.stdout.write('Created service %s\n' % service.name)
                    elif verbose:
                        self.stdout.write('Service %s for organisation %s')
                if verbose:
                    processed += 1
                transaction.commit()
            except Exception as e:
                if verbose:
                    skipped += 1
                self.stderr.write("Skipping %s %s (%s): %s" % (name, organisation_type, ods_code, e))
                transaction.rollback()

        if verbose:
            # First row is a header, so ignore it in the count
            self.stdout.write("Total records in file: {0}\n".format(rownum-1))
            self.stdout.write("Processed {0} records\n".format(processed))
            self.stdout.write("Skipped {0} records\n".format(skipped))
