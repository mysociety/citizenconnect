from django import forms
from django.forms.extras.widgets import SelectDateWidget

from organisations.models import Organisation


class ConcurrentFormMixin(object):
    """
    A Mixin for forms which need to check concurrent access to some model.
    """

    session_key = 'object_versions'

    # Set this in your form's __init__ to the model you want to check
    # concurrency for.
    # By not just checking self.instance, you have the option of checking
    # concurrent access to a different model, e.g. a foreign key
    concurrency_model = None


    def __init__(self, request=None, *args, **kwargs):
        """
        Overriden __init__ to take a request parameter
        """
        super(ConcurrentFormMixin, self).__init__(*args, **kwargs)
        # Store the request so we can use it later
        self.request = request
        # NOTE: On GET requests, your form class should call
        # self.set_version_in_session() after calling super(...)__init__()
        # and setting self.concurrency_model

    def set_version_in_session(self):
        """
        Save the current model version in the user's session
        """
        self.request.session.setdefault(self.session_key, {})
        self.request.session[self.session_key][self.concurrency_model.id] = self.concurrency_model.version
        self.request.session.modified = True

    def unset_version_in_session(self):
        """
        Delete the model version from the user's session
        """
        if self.request.session.get(self.session_key, False):
            if self.concurrency_model.id in self.request.session[self.session_key]:
                del self.request.session[self.session_key][self.concurrency_model.id]
                self.request.session.modified = True

    def concurrency_check(self):
        """
        Check that the user's version of the model is still the latest
        """
        if self.request.session.get(self.session_key, False):
            if self.concurrency_model.id in self.request.session[self.session_key]:
                session_version = self.request.session.get(self.session_key)[self.concurrency_model.id]
                return session_version == self.concurrency_model.version
        return False

    def save(self, *args, **kwargs):
        """
        Overriden save to unset the session variables we set in __init__
        This may still throw a RecordModifiedError, which you should catch to be
        totally sure you've not allowed concurrent editing, but it's quite a slim
        chance.
        """
        saved_object = super(ConcurrentFormMixin, self).save(*args, **kwargs)
        self.unset_version_in_session()
        return saved_object


class HoneypotModelForm(forms.ModelForm):

    # This is a honeypot field to catch spam bots. If there is any content in
    # it the form validation will fail and an appropriate error should be shown to
    # the user. This field is hidden by CSS in the form so should never be shown to
    # a user. Hopefully it will not be autofilled either.
    website = forms.CharField(
        label='Leave this blank',
        required=False,
    )

    def clean_website(self):
        # The field 'website' is a honeypot - it should be hidden from real
        # users. Anything that fills it in is probably a bot so reject the
        # submission.
        if self.cleaned_data.get('website'):
            raise forms.ValidationError("submission is probably spam")
        return ''


class LiveFeedFilterForm(forms.Form):
    """Form for processing filters on the live feed page, to filter problems
    and reviews by organisation and a date range."""

    organisation = forms.ModelChoiceField(required=False, queryset=Organisation.objects.all())
    start = forms.DateField(required=False)
    end = forms.DateField(required=False)
