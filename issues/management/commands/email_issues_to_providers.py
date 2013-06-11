import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.loader import get_template
from django.template import Context
from django.conf import settings

from issues.models import Problem

logger = logging.getLogger(__name__)


@transaction.commit_manually
class Command(BaseCommand):
    help = 'Email new problems to providers'

    def handle(self, *args, **options):
        new_problems = Problem.objects.all().filter(mailed=False)

        logger.info('{0} New problems to email'.format(len(new_problems)))

        if len(new_problems) > 0:
            # Get the template
            problem_template = get_template('organisations/new_problem_email.txt')
            # Loop over them and send
            for problem in new_problems:
                try:
                    self.send_problem(problem_template, problem)
                    problem.mailed = True
                    problem.save()
                    transaction.commit()
                except Exception as e:
                    logger.error('{0}'.format(e))
                    logger.error('Error mailing problem: {0}'.format(problem.reference_number))
                    transaction.rollback()

    def send_problem(self, template, problem):
        context = Context({'problem': problem, 'site_base_url': settings.SITE_BASE_URL})
        logger.info('Emailing problem reference number: {0}'.format(problem.reference_number))

        problem.organisation.trust.send_mail(
            subject='Care Connect: New Problem',
            message=template.render(context)
        )
