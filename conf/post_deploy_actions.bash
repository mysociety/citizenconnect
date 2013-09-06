#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..

# create/update the virtual environment
# NOTE: some packages are difficult to install if they are not site packages,
# for example xapian. If using these you might want to add the
# '--enable-site-packages' argument.
virtualenv_version="$(virtualenv --version)"
if [ "$(echo -e '1.7\n'$virtualenv_version | sort -V | head -1)" = '1.7' ]; then
    virtualenv_args="--system-site-packages"
else
    virtualenv_args="--no-site-packages"
fi 

virtualenv $virtualenv_args ../virtualenv-citizenconnect
source ../virtualenv-citizenconnect/bin/activate
pip install --requirement requirements.txt

# make sure that there is no old code (the .py files may have been git deleted)
find . -name '*.pyc' -delete

# get the database up to speed
./manage.py syncdb
./manage.py migrate

# make sure we've got the correct sass version
bundle install --path ../gems --deployment --binstubs ../gem-bin

# gather all the static files in one place
./manage.py collectstatic --noinput

# make a default site in the db if there's not one
./manage.py create_default_site
