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
        reader = csv.reader(open(filename), delimiter=',', quotechar='"')
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

        # ISSUE-343 - remove this when we have real ccg data in the spreadsheet
        demo_ccg = CCG.objects.get(pk=1)

        for row in reader:
            rownum += 1
            choices_id = row[0]
            name = row[1]
            trust = row[2]
            organisation_type_text = row[3]
            url = row[4]
            address_line1 = self.clean_value(row[5])
            address_line2 = self.clean_value(row[6])
            address_line3 = self.clean_value(row[7])
            city = self.clean_value(row[8])
            county = self.clean_value(row[9])
            lat = row[10]
            lon = row[11]
            last_updated = row[12]
            postcode = self.clean_value(row[13])
            ods_code = row[14]
            service_code = row[15]
            service_name = row[16]
            organisation_contact = row[17]

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
                                     # ISSUE-343 - remove this when we have real ccg associations
                                     'escalation_ccg': demo_ccg}
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
