from django.forms.widgets import RadioInput, RadioFieldRenderer
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

from .models import Problem

class CategoryRadioFieldRenderer(RadioFieldRenderer):
    """
    A custom RadioFieldRenderer for Category fields on issues
    which returns CategoryRadioInput widgets instead of normal
    RadioInputs
    """

    def __iter__(self):
        # Override this to return instances of CategoryRadioInput
        for i, choice in enumerate(self.choices):
            yield CategoryRadioInput(self.name, self.value, self.attrs.copy(), choice, i)

    def __getitem__(self, idx):
        # Override this to return instances of CategoryRadioInput
        choice = self.choices[idx] # Let the IndexError propogate
        return CategoryRadioInput(self.name, self.value, self.attrs.copy(), choice, idx)

class CategoryRadioInput(RadioInput):
    """
    A custom RadioInput widget which wraps the field label in an <abbr>
    tag so that we can display a helpful description of it to the user.
    """

    def render(self, name=None, value=None, attrs=None, choices=()):
        # Override render to put <abbr> in labels
        name = name or self.name
        value = value or self.value
        attrs = attrs or self.attrs
        if self.choice_value in Problem.CATEGORY_DESCRIPTIONS:
            description = Problem.CATEGORY_DESCRIPTIONS[self.choice_value] or ''
        else:
            description = ''
        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        choice_label = conditional_escape(force_unicode(self.choice_label))
        if description:
            choice_label = '<abbr title="%s">%s</abbr>' % (description, choice_label)
        return mark_safe(u'<label%s>%s %s</label>' % (label_for, self.tag(), choice_label))
