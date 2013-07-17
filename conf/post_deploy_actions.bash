#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

# create/update the virtual environment
# NOTE: some packages are difficult to install if they are not site packages,
# for example xapian. If using these you might want to add the
# '--enable-site-packages' argument.
virtualenv --no-site-packages ../virtualenv-citizenconnect
source ../virtualenv-citizenconnect/bin/activate
pip install --requirement requirements.txt

# make sure that there is no old code (the .py files may have been git deleted)
find . -name '*.pyc' -delete

# get the database up to speed
./manage.py syncdb
./manage.py migrate

# gather all the static files in one place
./manage.py collectstatic --noinput

# make a default site in the db if there's not one
./manage.py create_default_site
