from django.core.management.base import NoArgsCommand
from django.core import serializers

from organisations.models import Service, Organisation, OrganisationParent, CCG
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
        objects.extend(ccgs)

        # OrganisationParents
        org_parents = list(OrganisationParent.objects.all())
        for org_parent in org_parents:
            org_parent.email = 'organisation-parent@example.com'
            if org_parent.secondary_email:
                org_parent.secondary_email = 'organisation-parent@example.com'
        objects.extend(org_parents)

        # Organisations
        objects.extend(Organisation.objects.all())

        # Services
        objects.extend(Service.objects.all())

        # Reviews & Ratings
        objects.extend(Review.objects.all())
        objects.extend(Rating.objects.all())

        # News
        objects.extend(Article.objects.all())

        # Serialise things
        # This is a bit tricky because we don't want to serialise some
        # specific fields, but we want to get everything else.
        allowed_fields = set()

        # If you dump any more objects, make sure to add them to this list too
        # otherwise we won't dump any of their fields for sure
        model_classes = [CCG, OrganisationParent, Organisation, Service, Review, Rating, Article]

        for model_class in model_classes:
            # These two fields on the _meta are what
            # django.core.serializers.base uses when it checks fields to
            # serialize, so I've copied them here. The first covers normal
            # fields and foreign keys, the second covers many_to_many fields.
            allowed_fields.update([f.name for f in model_class._meta.local_fields])
            allowed_fields.update([f.name for f in model_class._meta.many_to_many])

        # We don't want any users that are connected to any models, because
        # they won't be in the db we'll load this dump into
        allowed_fields.discard('users')

        return serializers.serialize(
            'json',
            objects,
            indent=4,
            use_natural_keys=False,
            fields=allowed_fields
        )
