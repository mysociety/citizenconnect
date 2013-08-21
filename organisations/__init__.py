"""
Provides models, views and commands concerning the organisational structure of
the NHS.

Models are provided for CCGs, Organisation Parents (e.g. NHS Trusts) and
Organisations (e.g. Hospitals).

Views are provided to see all Organisations on a map, and in a summary table,
as well as for displaying the "dashboards" and other private interfaces that
users belonging to one of the ccgs/parents/organisations use to manage the
:model:`issues.Problem`s assigned to them.

Commands are provided to load ccgs/parents/organisations from CSV files, as
well as to load in users for them. A command is also provided to retrieve the
"average_recommendation_rating" of an Organisation from the NHS Choices API.

Several useful helper functions, libraries or mixins are also contained:
- interval_counts, for summarising data about Organisations in an efficient DB query
- dm, for calculating the double-metaphone of a string
- choices_api, a module providing a wrapper for interrogating the NHS Choices API
- SuperuserLogMiddleware, for logging access by users in the nhs_superusers role
- MailSendMixin, for models which need to send a welcome email when they're created
- auth, a module of helper functions and definitions for the user roles associated
  with ccgs, organisation parents and organisations
"""
