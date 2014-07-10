import logging
logger = logging.getLogger(__name__)
import os

from datetime import datetime
import hmac
import hashlib
from uuid import uuid4
from time import strftime, gmtime

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator
from django.db.models import Q
from django.utils.timezone import utc
from django.dispatch import receiver

from concurrency.fields import IntegerVersionField
from concurrency.api import concurrency_check

from citizenconnect.models import (
    AuditedModel,
    validate_file_extension,
    delete_uploaded_file
)
from .lib import base32_to_int, int_to_base32
from sorl.thumbnail import ImageField as sorlImageField


class ProblemQuerySet(models.query.QuerySet):
    """Custom queryset class for :model:`issues.Problem`"""

    # The fields to sort by. Used in the tables code.
    ORDER_BY_FIELDS_FOR_MODERATION_TABLE = ('priority', 'created')

    def order_for_moderation_table(self):
        """Sort by priority first, then by creation date.

        This is a crude way to ensure that the issues at the top of the
        moderation list are the ones that should be looked at next.

        This sorting could be improved by calculating a deadline for each
        problem and then sorting by that deadline. This would be the ideal as it
        would prevent high priority issues blocking long standing low priority
        ones.
        """
        args = self.ORDER_BY_FIELDS_FOR_MODERATION_TABLE
        return self.order_by(*args)

    def open_problems(self):
        """Return only open problems."""
        return self.all().filter(Q(status__in=Problem.OPEN_STATUSES))


class ProblemManager(models.Manager):
    """Custom manager class for :model:`issues.Problem`.

    Provides a series of methods that return specific subsets of Problems,
    in certain statuses.
    """
    use_for_related_fields = True

    # Note: it may be desirable in future to move some of the methods from
    # ProblemManager to ProblemQuerySet.

    def get_query_set(self):
        """Return a ProblemQuerySet."""
        return ProblemQuerySet(self.model, using=self._db)

    def open_problems(self):
        """Return only open problems"""
        return self.all().filter(Q(status__in=Problem.OPEN_STATUSES))

    def closed_problems(self):
        """Return only closed problems"""
        return self.all().filter(Q(status__in=Problem.CLOSED_STATUSES))

    def unmoderated_problems(self):
        """Return only problems which have not been moderated in any way.

        This excludes problems which have been "moderated" as requiring second
        tier moderation.
        """
        return self.all().filter(
            publication_status=Problem.NOT_MODERATED,
            requires_second_tier_moderation=False
        )

    def open_published_visible_problems(self):
        """Return only open, visible problems which have been published"""
        return self.open_problems().filter(publication_status=Problem.PUBLISHED,
                                           status__in=Problem.VISIBLE_STATUSES)

    def closed_published_visible_problems(self):
        """Return only closed, visible problems which have been published"""
        return self.closed_problems().filter(publication_status=Problem.PUBLISHED,
                                             status__in=Problem.VISIBLE_STATUSES)

    def all_published_visible_problems(self):
        """Return all visible problems which have been published"""
        return self.all().filter(publication_status=Problem.PUBLISHED,
                                 status__in=Problem.VISIBLE_STATUSES)

    def all_not_rejected_visible_problems(self):
        """Return all visible problems which have not been rejected"""
        return self  \
            .all()  \
            .filter(status__in=Problem.VISIBLE_STATUSES)  \
            .exclude(publication_status=Problem.REJECTED) \
            .exclude(requires_second_tier_moderation=True)

    def problems_requiring_second_tier_moderation(self):
        """Return all problems which need second tier moderation"""
        return self.all().filter(requires_second_tier_moderation=True)

    def requiring_confirmation(self):
        """Return all problems which have not had a confirmation email sent"""
        return self.filter(
            confirmation_sent__isnull=True,
            confirmation_required=True
        )

    def requiring_survey_to_be_sent(self):
        """Return all problems which require a survey email to be sent.

        Closed problems are sent a survey unless they've already been sent one,
        problems which don't have an email address are excluded.
        """
        return self.closed_problems().filter(survey_sent__isnull=True) \
            .exclude(status=Problem.ABUSIVE) \
            .exclude(reporter_email='')


class Problem(AuditedModel):
    """Stores problems reported by the public about organisations and services.

    Related to :model:`organisations.Organisation` and
    :model:`organisations.Service`
    """
    # Custom manager
    objects = ProblemManager()

    # Statuses that a Problem can be in
    NEW = 0
    ACKNOWLEDGED = 1
    RESOLVED = 2
    UNABLE_TO_RESOLVE = 3
    REFERRED_TO_OTHER_PROVIDER = 4
    UNABLE_TO_CONTACT = 5
    ABUSIVE = 6

    # Status integer to description mappings
    STATUS_CHOICES = (
        (NEW, 'Open'),
        (ACKNOWLEDGED, 'In Progress'),
        (RESOLVED, 'Closed'),
        (UNABLE_TO_RESOLVE, 'Unable to Resolve'),
        (REFERRED_TO_OTHER_PROVIDER, 'Referred to Another Provider'),
        (UNABLE_TO_CONTACT, 'Unable to Contact'),
        (ABUSIVE, 'Abusive/Vexatious'),
    )

    # Calculated status sets
    ALL_STATUSES = [status for status, description in STATUS_CHOICES]
    OPEN_STATUSES = [NEW, ACKNOWLEDGED]
    CLOSED_STATUSES = [RESOLVED, UNABLE_TO_RESOLVE, UNABLE_TO_CONTACT, ABUSIVE]
    HIDDEN_STATUSES = [ABUSIVE]
    VISIBLE_STATUSES = [status for status in ALL_STATUSES if status not in HIDDEN_STATUSES]
    VISIBLE_STATUS_CHOICES = [(status, description) for status, description in STATUS_CHOICES if status in VISIBLE_STATUSES]

    # Priorities that Problems can have.
    # The numerical value of the priorities should be chosen so that when sorted
    # ascending higher priorities come first. Please leave gaps in the range so that
    # future priority levels can be added without changing the existing ones.
    PRIORITY_HIGH = 20
    PRIORITY_NORMAL = 50

    # Priority value to description mappings
    PRIORITY_CHOICES = (
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_NORMAL, 'Normal'),
    )

    # Prefix that is prepended to the Problem id number to make a
    # "reference_number" - a slightly more human friendly reference for a
    # Problem
    PREFIX = 'P'

    # Publication statuses. Independent of the statuses above, these control
    # whether a problem is displayed, and how much of it is displayed.
    # They're modified during the moderation process.
    REJECTED = 0
    PUBLISHED = 1
    NOT_MODERATED = 2

    # Publication status integer to description mappings
    PUBLICATION_STATUS_CHOICES = (
        (NOT_MODERATED, "Not moderated"),
        (REJECTED, "Rejected"),
        (PUBLISHED, "Published")
    )

    # Commissioned options. Also modified during the moderation process, these
    # define whether the Service a problem is reported about is "locally"
    # commissioned or "nationally" commissioned. Locally commissioned services
    # are eventually the responsibility of a CCG, nationally commissioned ones
    # are the responsibility of a national body.
    LOCALLY_COMMISSIONED = 0
    NATIONALLY_COMMISSIONED = 1

    # Commissioned integer to description mappings
    COMMISSIONED_CHOICES = ((LOCALLY_COMMISSIONED, "Locally Commissioned"),
                            (NATIONALLY_COMMISSIONED, "Nationally Commissioned"))

    # Problem categories. Chosen by the person who reports a problem.
    CATEGORY_CHOICES = (
        (u'staff', u'Staff Attitude'),
        (u'access', u'Access to Service'),
        (u'delays', u'Delays'),
        (u'treatment', u'Your Treatment'),
        (u'communication', u'Communication'),
        (u'cleanliness', u'Cleanliness'),
        (u'equipment', u'Equipment'),
        (u'medicines', u'Medicines'),
        (u'food', u'Food'),
        (u'dignity', u'Dignity and Privacy'),
        (u'parking', u'Parking'),
        (u'lostproperty', u'Lost Property'),
        (u'other', u'Other'),
    )

    # Long descriptions of categories, used on the problem reporting form
    # to give more help about what each category means.
    CATEGORY_DESCRIPTIONS = {
        'staff': 'Bedside manner / staff attitude / care and compassion',
        'access': 'Difficulty getting appointments, long waiting times',
        'delays': 'Delays in care, e.g. referrals and test results',
        'treatment': 'Wrong advice / unsafe care / refusal of treatment / consent',
        'communication': 'Communications and administration e.g. letters',
        'cleanliness': 'Cleanliness and facilities',
        'equipment': 'Problems with equipment, aids and devices',
        'medicines': 'Problems with medicines',
        'food': '',  # TODO Add long description
        'dignity': 'Privacy, dignity, confidentiality',
        'parking': 'Problems with parking / charges',
        'lostproperty': 'Lost property',
        'other': ''
    }

    # Selecting some categories allows the reporter to then check an
    # additional box, which says that the problem is happening right now, and
    # this makes it automatically get a higher priority (see priorities above)
    CATEGORIES_PERMITTING_SETTING_OF_PRIORITY_AT_SUBMISSION = (
        'cleanliness',
        'communication',
        'delays',
        'dignity',
        'food',
        'staff',
        'medicines',
        'treatment',
    )

    # Preferred contact method options
    CONTACT_PHONE = 'phone'
    CONTACT_EMAIL = 'email'

    CONTACT_CHOICES = (
        (CONTACT_EMAIL, u'By Email'),
        (CONTACT_PHONE, u'By Phone')
    )

    # Names for transitions between statuses/states we might want to print in
    # a longer form as a description of what happened to the problem in that
    # transition. The format is:
    # 'field_name' : {
    #   'Description of transition': [<pairs of [old, new] values for the field which get this description>]
    # }
    TRANSITIONS = {
        'status': {
            'Acknowledged': [[NEW, ACKNOWLEDGED]],
            'Resolved': [[ACKNOWLEDGED, RESOLVED]]
        },
        'publication_status': {
            'Published': [[NOT_MODERATED, PUBLISHED], [REJECTED, PUBLISHED]],
            'Rejected': [[NOT_MODERATED, REJECTED], [PUBLISHED, REJECTED]],
            'Unmoderated': [[REJECTED, NOT_MODERATED], [PUBLISHED, NOT_MODERATED]],
        },
        'requires_second_tier_moderation': {
            'Referred': [[False, True]]
        },
    }

    # Which attrs are interesting to compare for revisions when determining
    # transitions. The order of these determines the order they are output
    # as a string if more than one transition happens in one change to the
    # model
    REVISION_ATTRS = ['publication_status', 'status', 'requires_second_tier_moderation']

    # Sources of problems. Used when problems are reported via the API to
    # indicate where that problem came from originally, allowing some stats
    # to be generated at some point.
    SOURCE_PHONE = 'phone'
    SOURCE_EMAIL = 'email'
    SOURCE_SMS = 'sms'
    SOURCE_TWITTER = 'twitter'
    SOURCE_FACEBOOK = 'facebook'
    SOURCE_MMS = 'mms'

    # Source value to description mappings
    SOURCE_CHOICES = (
        (SOURCE_EMAIL, 'Email'),
        (SOURCE_PHONE, 'Phone'),
        (SOURCE_SMS, 'SMS'),
        (SOURCE_TWITTER, 'Twitter'),
        (SOURCE_FACEBOOK, 'Facebook'),
        (SOURCE_MMS, 'MMS'),
    )

    # Allowable choices for the cobrand field
    COBRAND_CHOICES = [(cobrand, cobrand) for cobrand in settings.ALLOWED_COBRANDS]

    # The description of the problem given by the original reporter
    description = models.TextField(verbose_name='', validators=[MaxLengthValidator(2000)])
    # The original source of the problem when it's not reported through this
    # application (i.e.: it's come from the API)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, blank=True)
    # The name of the person who reported the problem
    reporter_name = models.CharField(max_length=200, blank=False, verbose_name='')
    # The phone number of the person who reported the problem
    reporter_phone = models.CharField(max_length=50, blank=True, verbose_name='')
    # The email address of the person who reported the problem
    reporter_email = models.EmailField(max_length=254, blank=True, verbose_name='')
    # Whether the person who reported the problem said they were under 16
    reporter_under_16 = models.BooleanField(default=False)
    # How the person who reported the problem would prefer to be contacted
    # by the people dealing with the problem
    preferred_contact_method = models.CharField(max_length=100, choices=CONTACT_CHOICES, default=CONTACT_EMAIL)
    # The category the person who reported the problem said their problem
    # fitted in.
    category = models.CharField(max_length=100,
                                choices=CATEGORY_CHOICES,
                                default='other',
                                db_index=True,
                                verbose_name='Please select the category that best describes your problem')
    # Whether the person who reported the problem would like it made public
    public = models.BooleanField()
    # Whether the person who reported the problem's name should be made public
    # This field is initially set by the reporter, but can be altered by the
    # moderation process to hide abusive names.
    public_reporter_name = models.BooleanField()
    # Whether the person who reported the problem would like their name made
    # public - this field records their original choice, regardless of what
    # happened later during moderation
    public_reporter_name_original = models.BooleanField(editable=False)
    # The current status of the problem
    status = models.IntegerField(default=NEW, choices=STATUS_CHOICES, db_index=True)
    # The current priority of the problem
    priority = models.IntegerField(default=PRIORITY_NORMAL, choices=PRIORITY_CHOICES, db_index=True)
    # The Organisation this problem was reported about
    organisation = models.ForeignKey('organisations.Organisation')
    # The service this problem was reported about
    service = models.ForeignKey('organisations.Service',
                                null=True,
                                blank=True,
                                verbose_name="Please select a department (optional)")
    # Whether the reporter was happy with the service they received after
    # reporting this problem - collected by surveying them after it's closed
    # in some way
    happy_service = models.NullBooleanField()
    # Whether the reporter was happy with the outcome after reporting this
    # problem - collected by surveying them after it's closed in some way
    happy_outcome = models.NullBooleanField()

    # How long whoever's dealing with the problem took to acknowledge it
    # Integer values represent time in minutes
    time_to_acknowledge = models.IntegerField(blank=True, null=True)
    # How long whoever's dealing with the problem took to resolve it
    time_to_address = models.IntegerField(blank=True, null=True)
    # When exactly the problem was resolved
    resolved = models.DateTimeField(blank=True, null=True)
    # A status field which determines how much of the problem is displayed to
    # the user, set during the moderation process.
    publication_status = models.IntegerField(default=NOT_MODERATED,
                                             blank=False,
                                             choices=PUBLICATION_STATUS_CHOICES,
                                             db_index=True)
    # A moderated version of the description the person who reported the
    # problem gave - entered during the moderation process.
    moderated_description = models.TextField(blank=True)
    # Whether this problem describes a "Breach of care" - set during the
    # moderation process
    breach = models.BooleanField(default=False, blank=False)
    # Whether this problem requires second tier moderation
    requires_second_tier_moderation = models.BooleanField(default=False, blank=False)
    # Whether this problem is locally or nationally commissioned
    commissioned = models.IntegerField(blank=True, null=True, choices=COMMISSIONED_CHOICES)
    # Which cobrand the user was using when they originally reported this
    # problem - so that we can present the survey in the same cobrand later
    cobrand = models.CharField(max_length=30, blank=False, choices=COBRAND_CHOICES, default=settings.ALLOWED_COBRANDS[0])
    # Whether this problem has been turned into a formal complaint by the
    # person dealing with it
    formal_complaint = models.BooleanField(default=False, blank=False)

    # Has this problem been sent to whoever's dealing with it
    mailed = models.BooleanField(default=False, blank=False, db_index=True)
    # When was a survey sent to the reporter
    survey_sent = models.DateTimeField(null=True, blank=True)
    # Is a confirmation email required - it's only required if they give us an
    # email address to send one too
    confirmation_required = models.BooleanField(default=False)
    # When was a confirmation sent to the reporter
    confirmation_sent = models.DateTimeField(null=True, blank=True)

    # The version of this probelm, used by django-concurrency to stop
    # concurrent editing of the problem by two different people
    version = IntegerVersionField()

    def __init__(self, *args, **kwargs):
        """Overriden __init__ to save an initial copy of
        public_reporter_name_original to check against when saving.

        See: http://stackoverflow.com/questions/1355150/django-when-saving-how-can-you-check-if-a-field-has-changed
        """
        super(Problem, self).__init__(*args, **kwargs)
        self.__initial_public_reporter_name_original = self.public_reporter_name_original

    @models.permalink
    def get_absolute_url(self):
        """Get the URL for viewing this Problem"""
        return ('problem-view', (),  {'pk': self.id, 'cobrand': 'choices'})

    @property
    def reference_number(self):
        """Get the reference number for this Problem"""
        return '{0}{1}'.format(self.PREFIX, self.id)

    def __unicode__(self):
        """Return a string representing this Problem"""
        return self.reference_number

    @property
    def reporter_name_display(self):
        """Get the reporter name we should display for this Problem.

        This method respects the public_reporter_name field on the problem.
        """
        if self.public_reporter_name and self.publication_status is not Problem.NOT_MODERATED:
            return self.reporter_name
        else:
            return "Anonymous"

    @property
    def summary(self):
        """Get a summary of the description for this Problem.

        This method respects the public field on the problem, and it's
        publication_status, and summarises the moderated_description.
        """
        if self.public:
            if self.publication_status == Problem.PUBLISHED:
                return self.summarise(self.moderated_description)
            elif self.publication_status == Problem.NOT_MODERATED:
                return "Awaiting moderation"
            else:
                return "Hidden"
        else:
            return "Private"

    @property
    def private_summary(self):
        """Get a summary of the description for this Problem for private pages.

        This method assumes that the caller has appropriate access to see the
        full details of the problem, and so ignores the public and
        publication_status fields, and summarises the original description.
        """
        return self.summarise(self.description)

    @property
    def has_elevated_priority(self):
        """Return whether this problem has a priority above normal"""
        return self.priority < Problem.PRIORITY_NORMAL

    @property
    def is_high_priority(self):
        """A problem is only a high priority if it's not closed"""
        return self.priority == Problem.PRIORITY_HIGH and not self.status in Problem.CLOSED_STATUSES

    def clean(self):
        """Custom model validation."""
        super(Problem, self).clean()

        # Check that one of phone or email is provided
        if not self.reporter_phone and not self.reporter_email:
            raise ValidationError('You must provide either a phone number or an email address')

        # Check that whichever prefered_contact_method is chosen, they actually provided it
        if self.preferred_contact_method == self.CONTACT_EMAIL and not self.reporter_email:
            raise ValidationError('You must provide an email address if you prefer to be contacted by email')
        elif self.preferred_contact_method == self.CONTACT_PHONE and not self.reporter_phone:
            raise ValidationError('You must provide a phone number if you prefer to be contacted by phone')

        self.validate_preferred_contact_method_and_reporter_phone(self.preferred_contact_method, self.reporter_phone)
        self.validate_reporter_under_16_and_public_reporter_name(self.reporter_under_16, self.public_reporter_name)
        if self.pk:
            self.validate_public_reporter_name(self.public_reporter_name, self.public_reporter_name_original)

    @classmethod
    def validate_preferred_contact_method_and_reporter_phone(cls, preferred_contact_method, reporter_phone):
        """Check that if the reporter of the problem prefers to be contacted
        by phone, they actually provided a phone number.
        """
        # this is a separate method so we can call it from form easily to share error message
        if preferred_contact_method == cls.CONTACT_PHONE and not reporter_phone:
            raise ValidationError('You must provide a phone number if you prefer to be contacted by phone')

    @classmethod
    def validate_reporter_under_16_and_public_reporter_name(cls, reporter_under_16, public_reporter_name):
        """Check that is the reporter is under 16, they cannot choose to show
        their name publically"""
        if reporter_under_16 is True and public_reporter_name is True:
            raise ValidationError('The reporter name cannot public if the reporter is under 16.')

    @classmethod
    def validate_public_reporter_name(cls, public_reporter_name, public_reporter_name_original):
        """Check that the name is not being made public at a later date when
        it should not be"""
        if public_reporter_name_original is False and public_reporter_name is True:
            raise ValidationError("May not change public_reporter_name to True when public_reporter_name_original is False")

    def summarise(self, field):
        """Summarise some plain text to 30 characters"""
        summary_length = 30
        if len(field) > summary_length:
            return field[:summary_length] + '...'
        else:
            return field

    def is_publicly_visible(self):
        """Return whether this problem is publicly visible.

        All problems are visible, unless: they have been moderated and
        rejected or they have been explicitly put in a hidden status.
        """
        if self.publication_status == Problem.REJECTED:
            return False
        elif int(self.status) in Problem.HIDDEN_STATUSES:
            return False
        else:
            return True

    def are_details_publicly_visible(self):
        """Return whether the problem's details should be publicly visible.

        They are visible if the problem is published and public is True.
        """
        return self.publication_status == Problem.PUBLISHED \
            and self.public \
            and int(self.status) not in Problem.HIDDEN_STATUSES

    def can_be_accessed_by(self, user):
        """Whether or not an issue is accessible to a given user.

        In practice the issue is publically accessible to everyone if it's
        publicly visible, or the user has access to the organisation it is
        assigned to.
        """
        return (self.is_publicly_visible() or self.organisation.can_be_accessed_by(user))

    def set_time_to_values(self):
        """Set the time_to_address, time_to_acknowledge and resolved times"""
        now = datetime.utcnow().replace(tzinfo=utc)
        minutes_since_created = self.timedelta_to_minutes(now - self.created)
        statuses_which_indicate_acknowledgement = [Problem.ACKNOWLEDGED,
                                                   Problem.RESOLVED]
        if self.time_to_acknowledge is None and int(self.status) in statuses_which_indicate_acknowledgement:
            self.time_to_acknowledge = minutes_since_created
        if self.time_to_address is None and int(self.status) == Problem.RESOLVED:
            self.time_to_address = minutes_since_created
            self.resolved = now

    def save(self, *args, **kwargs):
        """Override the default model save() method in order to populate
        time_to_acknowledge or time_to_address if appropriate."""
        concurrency_check(self, *args, **kwargs)  # Do a concurrency check

        if self.created:
            self.set_time_to_values()

        # It makes no sense to allow a problem reporter's name to be public when
        # the whole report is private. Change if needed when saving for the
        # first time.
        if not self.pk:
            if self.public is False:
                self.public_reporter_name = False

        if self.pk:
            # check that we are not trying to change public_reporter_name_original
            if self.public_reporter_name_original != self.__initial_public_reporter_name_original:
                raise Exception("Value of 'public_reporter_name_original' may not be changed after creation")
            self.validate_public_reporter_name(self.public_reporter_name, self.public_reporter_name_original)
        else:
            # set the public_reporter_name_original to match public_reporter_name
            self.public_reporter_name_original = self.public_reporter_name

        super(Problem, self).save(*args, **kwargs)  # Call the "real" save() method.
        self.__initial_public_reporter_name_original = self.public_reporter_name_original

    def check_token(self, token):
        """Check that a given token is valid for this Problem"""
        try:
            rand, hash = token.split("-")
        except:
            return False

        try:
            rand = base32_to_int(rand)
        except:
            return False

        if self.make_token(rand) != token:
            return False
        return True

    def make_token(self, rand):
        """Make a token for this Problem"""
        rand = int_to_base32(rand)
        hash = hmac.new(settings.SECRET_KEY, unicode(self.id) + rand, hashlib.sha1).hexdigest()[::2]
        return "%s-%s" % (rand, hash)

    @classmethod
    def timedelta_to_minutes(cls, timedelta):
        """Convert a timedelta into minutes"""
        days_in_minutes = timedelta.days * 60 * 24
        seconds_in_minutes = timedelta.seconds / 60
        return days_in_minutes + seconds_in_minutes


def obfuscated_upload_path_and_name(instance, filename):
    """Make an obfuscated image url"""
    base_image_path = 'images'
    date_based_directory = strftime('%m_%Y', gmtime())
    random_filename = uuid4().hex
    extension = os.path.splitext(filename)[1]
    # Note that django always wants FileField paths divided with unix separators
    return "/".join([base_image_path, date_based_directory, random_filename + extension])


class ProblemImage(AuditedModel):
    """Stores images related to a :model:`issues.Problem`"""

    # The image field
    image = sorlImageField(upload_to=obfuscated_upload_path_and_name, validators=[validate_file_extension])
    # The Problem this is related to
    problem = models.ForeignKey('issues.Problem', related_name='images')

    @classmethod
    def validate_problem(cls, problem):
        """check that the problem doesn't already have
        settings.MAX_IMAGES_PER_PROBLEM images"""
        if problem.images.all().count() >= settings.MAX_IMAGES_PER_PROBLEM:
            msg = "Problems can only have a maximum of {0} images.".format(settings.MAX_IMAGES_PER_PROBLEM)
            raise ValidationError(msg)

    def save(self, *args, **kwargs):
        """Override save() to check that there are no more than
        settings.MAX_IMAGES_PER_PROBLEM images on the given problem"""
        self.validate_problem(self.problem)
        super(ProblemImage, self).save(*args, **kwargs)


# post_delete handler to remove the image for a ProblemImage when it's deleted.
@receiver(models.signals.post_delete, sender=ProblemImage)
def article_post_delete_handler(sender, **kwargs):
    image = kwargs['instance']
    storage = image.image.storage
    path = image.image.path
    name = image.image.name
    delete_uploaded_file(storage, path, name, delete_empty_directory=True)
