#!/bin/bash

# abort on any errors
set -e

# Activate the venv
source ../virtualenv-citizenconnect/bin/activate

# Blank the db
./manage.py flush --noinput

# Trick South into thinking we've migrated
./manage.py migrate --fake

# Load data
./manage.py loaddata organisations/fixtures/staging_users.json
./manage.py loaddata organisations/fixtures/phase_2_organisations.json
./manage.py loaddata issues/fixtures/example_problems.json