import random
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers

from ...models import Problem
from organisations.models import Organisation

class Command(BaseCommand):
    args = '<number_to_create>'
    help = """Create some example problems based on existing problems, or a
    set of seed problems and assign them randomly to organisations, categories
     and statuses"""

    option_list = BaseCommand.option_list + (
        make_option(
            '--use-existing',
            action='store',
            dest='use_existing',
            default=False,
            help='Use existing problems in the DB as seeds.'
        ),
    )

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        use_existing = bool(options.get('use_existing'))

        if len(args) != 1:
            raise CommandError("Usage: ./manage.py create_example_problems number_to_create")

        number_of_problems = int(args[0])

        if use_existing:
            if verbosity >= 1:
                self.stdout.write("Basing generated problems on existing problems.")
            seed_problems = Problem.objects.all()
            if not seed_problems.count():
                raise CommandError("There are no existing problems in the database to base the new example ones on")
        else:
            # Load seed problems
            if verbosity >= 1:
                self.stdout.write("Basing generated problems on seed problems.")
            seed_problems = []
            seed_problem_path = os.path.join(
                os.abspath(os.path.dirname(__file__)),
                "..",
                "..",
                "fixtures",
                "seed_problems.json"
            )
            with open(seed_problem_path, 'r') as seed_problem_file:
                seed_problems = serializers.deserialize('json', seed_problem_file)


        i = 0
        organisations = Organisation.objects.all()

        if verbosity >= 1:
            self.stdout.write("Creating %i example problems\n" % number_of_problems)

        while i < number_of_problems:
            i += 1

            if verbosity >= 3:
                self.stdout.write("Creating problem %i of %i\n" % (i, number_of_problems))

            template_problem = seed_problems[int(random.random() * len(seed_problems))]
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
                new_problem.publication_status = Problem.NOT_MODERATED
            elif int(random.random() * 10 ) < 4:
                new_problem.publication_status = Problem.PUBLISHED
            else:
                new_problem.publication_status = Problem.REJECTED

            new_problem.category= Problem.CATEGORY_CHOICES[int(random.random() * len(Problem.CATEGORY_CHOICES))][0]
            new_problem.organisation = organisations[int(random.random() * len(organisations))]
            services = new_problem.organisation.services.all()
            if len(services) > 0:
                new_problem.service = services[int(random.random() * len(services))]
            new_problem.save()
