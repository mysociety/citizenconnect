from django.core.management.base import BaseCommand, CommandError

from ...choices_api import ChoicesAPI
from ...models import Organisation, Service

class Command(BaseCommand):
    help = 'Load organisations from the Choices API'

    def handle(self, *args, **options):

        api = ChoicesAPI()
        organisation_info_list = api.find_all_organisations('all')

        for organisation_info in organisation_info_list:
            organisation = Organisation(name=organisation_info['name'],
                                        organisation_type=organisation_info['organisation_type'],
                                        choices_id=organisation_info['choices_id'],
                                        ods_code=organisation_info['ods_code'],
                                        lat=organisation_info['coordinates']['lat'],
                                        lon=organisation_info['coordinates']['lon'])

            organisation.save()
            self.stdout.write('Created organisation %s\n' % organisation.name)
            if organisation.organisation_type == 'hospitals':
                service_info_list = api.get_organisation_services(organisation.organisation_type,
                                                                  organisation.choices_id)
                for service_info in service_info_list:
                    service = Service(organisation=organisation,
                                      name=service_info['name'],
                                      service_code=service_info['service_code'])
                    service.save()
                    self.stdout.write('Created service %s for %s\n' % (service.name, organisation.name))

