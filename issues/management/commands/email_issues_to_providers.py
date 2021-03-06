from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

from issues.models import Problem


@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email new problems to providers'

    def handle(self, *args, **options):
        verbosity = self.verbosity = int(options.get('verbosity'))
        new_problems = Problem.objects.all().filter(mailed=False)

        if verbosity >= 2:
            self.stdout.write("{0} New problems to email\n".format(len(new_problems)))

        if len(new_problems) > 0:
            # Get the template
            problem_template = get_template('organisations/new_problem_email.txt')
            # Loop over them and send
            for problem in new_problems:
                try:
                    self.send_problem(problem_template, problem)
                    # reload the problem from db to be sure that the version is fresh
                    problem = Problem.objects.get(pk=problem.id)
                    problem.mailed = True
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    if verbosity >= 1:
                        self.stderr.write("{0}\n".format(e))
                        self.stderr.write("Error mailing problem: {0}\n".format(problem.reference_number))
                    transaction.rollback()

    def send_problem(self, template, problem):
        context = Context({'problem': problem, 'site_base_url': settings.SITE_BASE_URL})
        if self.verbosity >= 2:
            self.stdout.write("Emailing problem reference number: {0}\n".format(problem.reference_number))

        problem.organisation.parent.send_mail(
            subject='Care Connect: New Problem',
            message=template.render(context)
        )
