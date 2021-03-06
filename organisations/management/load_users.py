import csv

from django.core.management.base import CommandError
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
from django.core import mail
from django.contrib.auth.models import User

from .. import auth


def from_csv(filename, org_parent_or_ccg_model):

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
            org_parent_or_ccg = org_parent_or_ccg_model.objects.get(code=code)
        except org_parent_or_ccg_model.DoesNotExist:
            raise CommandError("Could not find a {0} with the code {1}".format(org_parent_or_ccg_model.__name__, code))

        # get the user, creating if not found
        user, created = User.objects.get_or_create(username=username, email=email)

        # Ensure that the user is added to the org and the correct group, will
        # be no-ops if already done.
        org_parent_or_ccg.users.add(user)
        user.groups.add(org_parent_or_ccg.default_user_group())

        if created:
            user.set_password(auth.create_initial_password())
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
