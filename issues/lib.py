try:
    from collections import OrderedDict
except ImportError:
    # python 2.6 or earlier, use backport
    from ordereddict import OrderedDict

import reversion

"""
Returns a hash of attributes which have changed from the old_version to the new_version.
Restricts the attributes compared to the list of interesting_attrs passed in.
"""
def changed_attrs(old_version, new_version, interesting_attrs):
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

"""
Returns an English string describing a hash of changes, drawn from a dictionary of transition descriptions.
EG: Acknowledged, Moderated and Published, Resolved, etc.
"""
def changes_as_string(changed_attrs, transitions):
    changes = []
    for attr, change in changed_attrs.items():
        for transition_description, possible_transitions in transitions[attr].items():
            for transition in possible_transitions:
                if transition == change:
                    changes.append(transition_description)
    if len(changes) > 2:
        return '{0} and {1}'.format(', '.join(changes[:-1]), changes[-1])
    else:
        return ' and '.join(changes)

"""
Use changed_attrs and changes_as_string to produce a list of changes in English
for a given model
"""
def changes_for_model(model):
    changes = []
    history = reversion.get_for_object(model).order_by("revision__date_created")
    for index, version in enumerate(history):
        # We're only interested in changes
        if index > 0:
            old = history[index - 1].field_dict
            new = version.field_dict
            changed = changed_attrs(old, new, model.REVISION_ATTRS)
            if changed:
                change_string = changes_as_string(changed, model.TRANSITIONS)
                if change_string:
                    changes.append({"user":version.revision.user, "description":change_string})
    return changes
