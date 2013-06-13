import csv

from django.core.management.base import BaseCommand, CommandError
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.core import mail

from ...models import CCG
from ... import auth


class Command(BaseCommand):
    help = "Create user accounts for CCGs from a csv"

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
            ccg_code = row['Code']

            ccg = CCG.objects.get(code=ccg_code)

            user, created = ccg.users.get_or_create(username=username, email=email)

            if created:
                context = Context({
                    'user': user,
                    'site_base_url': settings.SITE_BASE_URL
                })
                mail.send_mail(
                    subject=subject_template.render(context),
                    message=message_template.render(context),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False
                )
