from django.core.management.base import NoArgsCommand
from django.core import serializers

from organisations.models import Organisation, OrganisationParent, CCG
from reviews_display.models import Review, Rating
from news.models import Article


class Command(NoArgsCommand):
    """
    This command dumps data from this site into a .json file that can
    be loaded with ./manage.py loaddata or saved as a fixture.

    Specifically, it dumps the following models:
    organisations.Organisation
    organisations.OrganisationParent
    organisations.CCG
    reviews_display.Review
    reviews_display.Rating
    news.Article

    For CCGs and OrganisationParents, the existing email addresses will be
    replaced by dummy email addresses:
    organisation-parent@example.com
    ccg@example.com
    and the existing users will be removed.

    For reviews, the data is left as-is, since it's come from the public NHS
    api anyway.

    For news, the data is left as-is, since it's come from the public news
    page.
    """

    help = "Dump out organisation, review and news data from this site, " \
    "anonymising or removing all the personal data. Note: problems are not " \
    "dumped, because anonymising them is tricky, and transferring them to a " \
    "separate instance doesn't necessarily make any sense."

    def handle_noargs(self, *args, **options):
        objects = []

        # CCGs
        ccgs = list(CCG.objects.all())
        for ccg in ccgs:
            ccg.email = 'ccg@example.com'
            ccg.users = []
        objects.extend(ccgs)

        # OrganisationParents
        org_parents = list(OrganisationParent.objects.all())
        for org_parent in org_parents:
            org_parent.email = 'organisation-parent@example.com'
            if org_parent.secondary_email:
                org_parent.secondary_email = 'organisation-parent@example.com'
            org_parent.users = []
        objects.extend(org_parents)

        # Organisations
        objects.extend(Organisation.objects.all())

        # Reviews & Ratings
        objects.extend(Review.objects.all())
        objects.extend(Rating.objects.all())

        # News
        objects.extend(Article.objects.all())

        # Serialise things
        return serializers.serialize('json', objects, indent=4, use_natural_keys=False)
