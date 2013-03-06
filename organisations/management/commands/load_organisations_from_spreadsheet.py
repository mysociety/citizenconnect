import csv
from optparse import make_option

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point

from ...models import Organisation, Service

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
            help='Delete existing organisations and services, and associated problems and questions'),
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

        type_mappings = {'HOS': 'hospitals',
                         'GP': 'gppractices'}
        for row in reader:
            rownum += 1
            if rownum == 1:
                continue
            choices_id = row[0]
            name = row[1]
            organisation_type_text = row[2]
            url = row[3]
            address_line1 = self.clean_value(row[4])
            address_line2 = self.clean_value(row[5])
            address_line3 = self.clean_value(row[6])
            city = self.clean_value(row[7])
            county = self.clean_value(row[8])
            lat = row[9]
            lon = row[10]
            last_updated = row[11]
            postcode = self.clean_value(row[12])
            ods_code = row[13]
            service_code = row[14]
            service_name = row[15]
            organisation_contact = row[16]
            organisation_contact_type = row[17]

            if organisation_type_text not in type_mappings:
                if verbose:
                    print "Unknown organisation type %s, skipping" % organisation_type_text
                continue

            organisation_type = type_mappings[organisation_type_text]
            organisation_defaults = {'choices_id':choices_id,
                                     'name': name,
                                     'organisation_type': organisation_type,
                                     'point': Point(float(lon), float(lat)),
                                     'address_line1': address_line1,
                                     'address_line2': address_line2,
                                     'address_line3': address_line3,
                                     'city': city,
                                     'county': county,
                                     'postcode': postcode}
            try:
                organisation, organisation_created = Organisation.objects.get_or_create(ods_code=ods_code,
                                                                           defaults=organisation_defaults)
                if update:
                    Organisation.objects.filter(id=organisation.id).update(**organisation_defaults)
                service = None
                if service_name and service_name != 'NULL':
                    service_defaults = {'name': service_name }
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
                transaction.commit()
            except Exception as e:
                self.stderr.write("Skipping %s %s (%s): %s" % (name, organisation_type, ods_code, e))
                transaction.rollback()
