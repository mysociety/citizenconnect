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
use to access the citizenconnect admin interface. Don't bother, we'll load
a precreated one in a minute.

### Add all the tables and columns we manage with South

    ./manage.py migrate

### Gather all the static files in one place
    ./manage.py collectstatic --noinput

### Add some users which are useful for development
    ./manage.py loaddata organisations/fixtures/development_users.json

### Load demo CCGs, Organisation Parents and Organisations
    ./manage.py loaddata organisations/fixtures/demo_ccg.json
    ./manage.py loaddata organisations/fixtures/demo_organisation_parent.json
    ./manage.py loaddata organisations/fixtures/phase_2_organisations.json

### If you ever need to reload the data, you can run
    ./manage.py flush
    ./manage.py migrate --fake
(Because you just flushed South's records of what was migrated, but the structure is still the same)
Then you can re-run the loaddata commands from above

Testing
------------

    ./manage.py test

The tests are run with a custom test runner, which uses the setting `IGNORE_APPS_FOR_TESTING` to ignore
third-party apps and django tests, so that you don't have to list all the internal apps.

There are also some Selenium tests, currently using Chrome and ChromeDriver, so make sure you have a recent (> v26)
version installed.

If you're on a headless server, eg: in a vagrant box, you'll need to install
the google-chrome-stable and xvfb packages (see the commented out section of
/conf/packages), as well as downloading the pre-built ChromeDriver binary.

To get google-chrome-stable, you need to add Google's repository to your apt-get (the version of chromium in 12.04 at least is too old):

    # Add Google's key for apt
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

    # Add their repo to your sources list
    sudo sh -c 'echo deb http://dl.google.com/linux/chrome/deb/ stable main > /etc/apt/sources.list.d/google.list'

    # Update your package list
    sudo apt-get update

    # Install google chrome
    sudo apt-get install google-chrome-stable

To get ChromeDriver, download the appropriate zip directly from: https://code.google.com/p/chromedriver/downloads/list and put the binary somewhere on your $PATH.

After installing them, start Xvfb with:

    Xvfb :99 -ac &

And export your display variable:

    export DISPLAY=:99

You might want to make that happen at every startup with the appropriates
lines in `/etc/rc.local` and `~/.bashrc`

Alternatively, if you don't want to run the selenium tests, set SKIP_BROWSER_TESTS to true in your environment.
