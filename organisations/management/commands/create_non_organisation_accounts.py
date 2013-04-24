import csv
from optparse import make_option

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.core import mail

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
        reader = csv.DictReader(open(filename), delimiter=',', quotechar='"')
        verbose = options['verbose']

        if verbose:
            processed = 0
            skipped = 0

        subject_template = get_template('organisations/generic_intro_email_subject.txt')
        message_template = get_template('organisations/generic_intro_email_message.txt')

        # Start at 1 as the first row is used to read in the headers.
        rownum = 1

        for row in reader:
            rownum += 1

            name = row["Name"]
            email = row["Email"]
            try:

                is_super = self.true_if_x(row["NHS Superusers"], rownum)
                is_case_handler = self.true_if_x(row["Case Handlers"], rownum)
                is_second_tier_moderator = self.true_if_x(row["Second Tier Moderators"], rownum)
                is_ccc = self.true_if_x(row["Customer Contact Centre"], rownum)

                user, created = User.objects.get_or_create(username=name, email=email)
                if is_super:
                    user.groups.add(auth.NHS_SUPERUSERS)
                if is_case_handler:
                    user.groups.add(auth.CASE_HANDLERS)
                if is_second_tier_moderator:
                    user.groups.add(auth.SECOND_TIER_MODERATORS)
                if is_ccc:
                    user.groups.add(auth.CUSTOMER_CONTACT_CENTRE)

                if verbose:
                    processed += 1
                transaction.commit()
                if created:
                    context = Context({
                        'user': user,
                        'site_base_url': settings.SITE_BASE_URL
                    })
                    mail.send_mail(subject=subject_template.render(context),
                                   message=message_template.render(context),
                                   from_email=settings.DEFAULT_FROM_EMAIL,
                                   recipient_list=[email],
                                   fail_silently=False)

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

