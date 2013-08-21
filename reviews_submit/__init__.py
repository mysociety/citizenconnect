"""
Provides models, views and forms for submitting reviews and ratings of
:model:`organisations.Organisation`s, and management commands to send those
reviews and ratings to the NHS Choices API.

Also provides a command to cleanup the local database of reviews that have
been sent, and a command to import a set of questions and answers from the XML
that NHS Choices provides to describe what Ratings are available.
"""
