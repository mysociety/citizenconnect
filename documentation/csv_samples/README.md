# Sample CSV files

Note that these files are used by the `organisations/tests/csv_import.py` tests. If you change them here be sure to run that test to see that they are still valid.

There is proper documentation in `documentation/csv_formats.md`.

The management commands that use these files are:

- `organisations/management/commands/load_ccgs_from_csv.py`
- `organisations/management/commands/load_organisation_parents_from_csv.py`
- `organisations/management/commands/load_organisations_from_csv.py`
- `organisations/management/commands/load_organisation_parent_users_from_csv.py`
- `organisations/management/commands/load_ccg_users_from_csv.py`
- `organisations/management/commands/load_other_users_from_csv.py`
