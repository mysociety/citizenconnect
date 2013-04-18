import csv
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from organisations import auth

class Command(BaseCommand):
    help = "Create accounts in groups that aren't directly associated with CCGs or organisations from a spreadsheet"

    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            action='store_true',
            dest='verbose',
            default=False,
            help='Show verbose output'),
        )

    @transaction.commit_manually
    def handle(self, *args, **options):
        filename = args[0]
        reader = csv.reader(open(filename), delimiter=',', quotechar='"')
        rownum = 0
        verbose = options['verbose']

        if verbose:
            processed = 0
            skipped = 0

        for row in reader:
            rownum += 1
            if rownum == 1:
                continue
            name = row[0]
            email = row[1]
            try:

                is_super = self.true_if_x(row[2], rownum)
                is_case_handler = self.true_if_x(row[3], rownum)
                is_question_answerer = self.true_if_x(row[4], rownum)
                is_cqc = self.true_if_x(row[5], rownum)
                is_second_tier_moderator = self.true_if_x(row[6], rownum)
                is_ccc = self.true_if_x(row[7], rownum)

                user, created = User.objects.get_or_create(username=name, email=email)
                if is_super:
                    user.groups.add(auth.NHS_SUPERUSERS)
                if is_case_handler:
                    user.groups.add(auth.CASE_HANDLERS)
                if is_question_answerer:
                    user.groups.add(auth.QUESTION_ANSWERERS)
                if is_cqc:
                    user.groups.add(auth.CQC)
                if is_second_tier_moderator:
                    user.groups.add(auth.SECOND_TIER_MODERATORS)
                if is_ccc:
                    user.groups.add(auth.CUSTOMER_CONTACT_CENTRE)

                if verbose:
                    processed += 1
                transaction.commit()
            except Exception as e:
                if verbose:
                    skipped += 1
                self.stderr.write("Skipping %s: %s" % (name, e))
                transaction.rollback()
        if verbose:
            # First row is a header, so ignore it in the count
            self.stdout.write("Total records in file: {0}\n".format(rownum-1))
            self.stdout.write("Processed {0} records\n".format(processed))
            self.stdout.write("Skipped {0} records\n".format(skipped))

    def true_if_x(self, cell, rownum):
        if cell == 'x':
            return True
        elif cell.strip() == '':
            return False
        else:
            raise Exception("Bad value in row %d: %s\n" % (rownum, cell))

