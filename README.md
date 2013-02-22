Citizen Connect
===============

Installation
------------

Something like the following, customised to your particular environment or set
up:

### Clone the repo
    mkdir citizenconnect
    cd citizenconnect
    git clone https://github.com/mysociety/citizenconnect.git

### Install the required software packages
Assuming you're on a debian/ubuntu server, you can look in `conf/packages` for a list, for other OSes, google to see what they're called on your system.

### Make sure you are using a UTF8 locale
    sudo update-locale LANG=en_GB.utf8

Note: you might need to reinitialise the postgres cluster to use the new locale, if you get complaints from the create database script about a missing UTF8 locale, or it not matching LATIN1, you can run the following to reinitialise it. But BEWARE, it deletes everything to do with this postgres cluster, ie: all your data!

    sudo pg_dropcluster --stop 9.1 main
    sudo pg_createcluster --locale=en_GB.utf8 --start 9.1 main

You can replace `9.1` with your postgres version, and `en_GB.utf8` with another UFT8 locale if you desire.

### Create the GeoDjango database template
    sudo -u postgres bin/create_template_postgis-debian.sh

The provided script should work for Debian based hosts, see https://docs.djangoproject.com/en/1.4/ref/contrib/gis/install/#spatialdb-template for other instructions.

### Create a postgres user and database from the template
    sudo -u postgres psql
    postgres=### CREATE USER citizenconnect WITH PASSWORD 'citizenconnect' CREATEDB;
    CREATE ROLE
    postgres=### CREATE DATABASE citizenconnect WITH TEMPLATE template_postgis OWNER citizenconnect;
    CREATE DATABASE

### Set up a python virtual environment, activate it
    virtualenv --no-site-packages virtualenv-citizenconnect
    source virtualenv-citizenconnect/bin/activate

### Install required python packages
    cd citizenconnect
    pip install --requirement requirements.txt

### Alter conf/general.yml as per your set up
    cp conf/general.yml-example conf/general.yml

### Set up database
    ./manage.py syncdb

This will ask you if you wish to create a Django superuser, which you'll
use to access the citizenconnect admin interface. You can always do it later with
`./manage.py createsuperuser`, but there's no harm in doing it now either,
just remember the details you choose!

    ./manage.py migrate

### To reload the initial data

    ./manage.py flush

### Gather all the static files in one place
    ./manage.py collectstatic --noinput
