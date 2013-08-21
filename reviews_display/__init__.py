"""
Provides models and views for storing and displaying reviews and ratings of
:model:`organisations.Organisation`s, and management commands to retrieve those
reviews and ratings from the NHS Choices API.

Also provides a command to cleanup the local database of reviews that are
older than a set date.

A helper module: reviews_api, is also provided. This is a wrapper around the
review aspects of the NHS Choices API, to make it easier to retrieve reviews
from it.
"""
