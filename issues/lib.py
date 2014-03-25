try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

import reversion

from django.core.serializers.base import DeserializationError


def changed_attrs(old_version, new_version, interesting_attrs):
    """
    Returns a hash of attributes which have changed from the old_version to the new_version.
    Restricts the attributes compared to the list of interesting_attrs passed in.
    """
    # Use an OrderedDict so that we preserve the order from interesting_attrs
    changed = OrderedDict()
    for attr in interesting_attrs:
        if attr in old_version and attr not in new_version:
            changed[attr] = [old_version[attr], None]
        elif attr in new_version and attr not in old_version:
            changed[attr] = [None, new_version[attr]]
        elif old_version[attr] != new_version[attr]:
            changed[attr] = [old_version[attr], new_version[attr]]
    return changed


def changes_as_string(changed_attrs, transitions):
    """
    Returns an English string describing a hash of changes, drawn from a
    dictionary of transition descriptions.
    EG: Acknowledged, Moderated and Published, Resolved, etc.
    """
    changes = []
    if not changed_attrs:
        return ''
    for attr, change in changed_attrs.items():
        for transition_description, possible_transitions in transitions[attr].items():
            for transition in possible_transitions:
                if transition == change:
                    changes.append(transition_description)
    if len(changes) > 2:
        return '{0} and {1}'.format(', '.join(changes[:-1]), changes[-1])
    else:
        return ' and '.join(changes)


def changed_attrs_by_version(model, interesting_attrs):
    """Produce an ordered dictionary of changed attrs for a model, keyed by version"""
    changed = OrderedDict()
    history = reversion.get_for_object(model).order_by("revision__date_created")
    for index, version in enumerate(history):
        # We're only interested in changes
        if index > 0:
            try:
                old = history[index - 1].field_dict
                new = version.field_dict
                changed[version] = changed_attrs(old, new, interesting_attrs)
            except DeserializationError:
                # Django's deserialisation framework gets upset if it tries to get
                # a model instance from some json or xml and the instance has fields
                # which are no longer in the Model - eg: because you just deleted them
                # in a South migration.
                # In Django 1.5 you can tell it to ignorenonexistent and it'll just work
                # which django-reversion helpfully does since:
                # https://github.com/etianen/django-reversion/issues/221
                # In Django 1.4 there is not this option, and thus django-reversion
                # hits a block when trying to get its' historical versions of the model
                # and passes on this error to us. At which point we can nothing useful
                # with it, and so we just ignore that point in history.
                pass
    return changed


def changes_for_model(model):
    """Return a list of changes in English for a given model."""
    change_strings = []
    for version, changes in changed_attrs_by_version(model, model.REVISION_ATTRS).items():
        change_string = changes_as_string(changes, model.TRANSITIONS)
        if change_string:
            change_strings.append({
                "user": version.revision.user,
                "description": change_string,
                "when": version.revision.date_created
            })

    return change_strings


# Miss out i l o u
base32_digits = "0123456789abcdefghjkmnpqrstvwxyz"


class MistypedIDException(Exception):
    pass


def base32_to_int(s):
    """Convert a base 32 string to an integer"""
    mistyped = False
    if s.find('o') > -1 or s.find('i') > -1 or s.find('l') > -1:
        s = s.replace('o', '0').replace('i', '1').replace('l', '1')
        mistyped = True
    decoded = 0
    multi = 1
    while len(s) > 0:
        decoded += multi * base32_digits.index(s[-1:])
        multi = multi * 32
        s = s[:-1]
    if mistyped:
        raise MistypedIDException(decoded)
    return decoded


def int_to_base32(i):
    """Converts an integer to a base32 string"""
    enc = ''
    while i >= 32:
        i, mod = divmod(i, 32)
        enc = base32_digits[mod] + enc
    enc = base32_digits[i] + enc
    return enc
