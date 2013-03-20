import random

from django.db import transaction, IntegrityError
from django.core.management.base import BaseCommand, CommandError

from ...models import Problem, IssueModel
from organisations.models import Organisation

class Command(BaseCommand):
    help = """Create some example problems based on existing problems and assign them
    randomly to organisations, categories and statuses"""

    def handle(self, *args, **options):

        number_of_problems = int(args[0])

        i = 0
        existing_problems = Problem.objects.all()
        organisations = Organisation.objects.all()

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
            if new_problem.public == 1:
                if int(random.random() * 10) < 8:
                    new_problem.moderated = 1
                    if int(random.random() * 10) < 8:
                        new_problem.publication_status = 1
            new_problem.category= IssueModel.CATEGORY_CHOICES[int(random.random() * len(IssueModel.CATEGORY_CHOICES))][0]
            new_problem.organisation = organisations[int(random.random() * len(organisations))]
            services = new_problem.organisation.services.all()
            if len(services) > 0:
                new_problem.service = services[int(random.random() * len(services))]
            new_problem.save()
