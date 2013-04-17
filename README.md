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

Or if you're using OS X with Homebrew installed:

    ./bin/create_template_postgis-mac.sh

The provided scripts should work for Debian and OS X based hosts, see https://docs.djangoproject.com/en/1.4/ref/contrib/gis/install/#spatialdb-template for other instructions.

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
use to access the citizenconnect admin interface. Don't bother, we'll load
a precreated one in a minute.

### Add all the tables and columns we manage with South

    ./manage.py migrate

### Gather all the static files in one place
    ./manage.py collectstatic --noinput

### Add some users which are useful for development
    ./manage.py loaddata organisations/fixtures/development_users.json

### Load the organisations we deal with
    ./manage.py loaddata organisations/fixtures/phase_2_organisations.json

### If you ever need to reload the data, you can run
    ./manage.py flush
    ./manage.py migrate --fake
(Because you just flushed South's records of what was migrated, but the structure is still the same)
Then you can re-run the loaddata commands from above

