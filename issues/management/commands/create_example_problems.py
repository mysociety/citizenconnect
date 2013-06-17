import random

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError

from ...models import Problem
from organisations.models import Organisation

class Command(BaseCommand):
    help = """Create some example problems based on existing problems and assign them
    randomly to organisations, categories and statuses"""

    def handle(self, *args, **options):

        if len(args) != 1:
            raise CommandError("Usage: ./manage.py create_example_problems number_to_create")

        number_of_problems = int(args[0])

        i = 0
        existing_problems = Problem.objects.all()
        organisations = Organisation.objects.all()

        if not existing_problems.count():
            raise CommandError("There are no existing problems in the database to base the new example ones on")

        while i <= number_of_problems:
            i += 1
            template_problem = existing_problems[int(random.random() * len(existing_problems))]
            new_problem = Problem(description=template_problem.description,
                                  reporter_name=template_problem.reporter_name,
                                  reporter_phone=template_problem.reporter_phone,
                                  reporter_email=template_problem.reporter_email,
                                  public_reporter_name=template_problem.public_reporter_name,
                                  preferred_contact_method=template_problem.preferred_contact_method,
                                  source=template_problem.source,
                                  mailed=template_problem.mailed,
                                  status=template_problem.status,
                                  happy_service=template_problem.happy_service,
                                  happy_outcome=template_problem.happy_outcome,
                                  time_to_acknowledge=template_problem.time_to_acknowledge,
                                  time_to_address=template_problem.time_to_address)

            new_problem.public = int(random.random() * 2)

            # set the publication_status
            if int(random.random() * 10 ) < 4:
                new_problem.publication_status = Problem.NOT_MODERATED_PUB
            elif int(random.random() * 10 ) < 4:
                new_problem.publication_status = Problem.PUBLISHED
            else: 
                new_problem.publication_status = Problem.HIDDEN

            new_problem.category= Problem.CATEGORY_CHOICES[int(random.random() * len(Problem.CATEGORY_CHOICES))][0]
            new_problem.organisation = organisations[int(random.random() * len(organisations))]
            services = new_problem.organisation.services.all()
            if len(services) > 0:
                new_problem.service = services[int(random.random() * len(services))]
            new_problem.save()
