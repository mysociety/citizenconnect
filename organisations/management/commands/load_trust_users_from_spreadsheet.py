import csv

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template

from ...models import Trust, CCG
from ... import auth


class Command(BaseCommand):
    help = "Create user accounts for trusts from a csv"

    def handle(self, *args, **options):
        if len(args) is 0:
            raise CommandError("Please supply a csv file to import from")

        filename = args[0]
        reader = csv.DictReader(open(filename), delimiter=',', quotechar='"')

        subject_template = get_template('organisations/generic_intro_email_subject.txt')
        message_template = get_template('organisations/generic_intro_email_message.txt')

        rownum = 1

        for row in reader:
            rownum += 1
            username = row["Username"]
            email = row["Email"]
            trust_code = row['Code']

            trust = Trust.objects.get(code=trust_code)

            user, created = trust.users.get_or_create(username=username, email=email)
