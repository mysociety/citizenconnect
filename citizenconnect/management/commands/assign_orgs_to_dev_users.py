import random

from django.core.management.base import NoArgsCommand, CommandError
from django.contrib.auth import User

from organisations.models import OrganisationParent, CCG


class Command(NoArgsCommand):
    """
    This command assigns all the OrganisationParent and CCG models in the DB
    to one of the users in organisations/fixtures/development_users.json

    CCGs are randomly assigned one of the two CCG users, OrganisationParents
    are assigned to the gp surgery user if they have any gps, and the trust
    user otherwise.
    """

    help = "Assign users from the development_users.json fixture to the " \
    "CCG and OrganisationParent models in the database. Note: you must have " \
    "already loaded the development_users fixture for this to work."


    def handle_noargs(self, *args, **options):
        # First check that we have the development users we expect
        try:
            ccg_user = User.objects.get(username='ccg')
            other_ccg_user = User.objects.get(username='other_ccg')
            ccg_users = [ccg_user, other_ccg_user]
            trust_user = User.objects.get(username='trust')
            gp_surgery_user = User.objects.get(username='gp_surgery_user')
        except User.DoesNotExist as e:
            raise CommandError("Could not find required user from development_users.json. {0}".format(e))

        # CCGs
        ccgs = list(CCG.objects.all())
        for ccg in ccgs:
            user = random.choice(ccg_users)
            ccg.users = [user]
            ccg.save()

        # OrganisationParents
        org_parents = list(OrganisationParent.objects.all())
        for org_parent in org_parents:
            if org_parent.organisations.filter(organisation_type='gppractices').exists():
                org_parent.users.add(gp_surgery_user)
            else:
                org_parent.users.add(trust_user)
                org_parent.save()
