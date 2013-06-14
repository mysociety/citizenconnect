import csv

from django.core.management.base import CommandError
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.core import mail

from .. import auth

def from_csv(filename, trust_or_ccg_model):

    reader = csv.DictReader(open(filename), delimiter=',', quotechar='"')

    subject_template = get_template('organisations/generic_intro_email_subject.txt')
    message_template = get_template('organisations/generic_intro_email_message.txt')

    rownum = 1

    for row in reader:
        rownum += 1
        username = row["Username"]
        email = row["Email"]
        code = row['Code']

        try:
            trust_or_ccg = trust_or_ccg_model.objects.get(code=code)
        except trust_or_ccg_model.DoesNotExist:
            raise CommandError("Could not find a {0} with the code {1}".format(trust_or_ccg_model.__name__, code))

        user, created = trust_or_ccg.users.get_or_create(username=username, email=email)

        if created:
            user.set_password(auth.create_initial_password())
            user.groups.add(trust_or_ccg.default_user_group())
            user.save()

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
