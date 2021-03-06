Citizen Connect
===============

Documentation
-------------
Various documentation is available in the `documentation` folder. For an overview of what this project is about and does, see `conf/OVERVIEW.md`.

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

### Install required ruby packages
    bundle install --path ../gems --binstubs ../gem-bin

### Alter conf/general.yml as per your set up
    cp conf/general.yml-example conf/general.yml

### Set up database
    ./manage.py syncdb

This will ask you if you wish to create a Django superuser, which you'll
use to access the citizenconnect admin interface. Don't bother, we'll load
a precreated one in a minute.

### Add all the tables and columns we manage with South
    ./manage.py migrate

### Create/Update the default site to be something useful

This is needed because we emit fully qualified redirects, amongst other reasons.

Make sure you have set the `SITE_BASE_URL` setting to something accurate
(probably `localhost:8000`) before running this.
    ./manage.py create_default_site

### Gather all the static files in one place
    ./manage.py collectstatic --noinput

Loading Data
------------

At the very least, the site will need some CCGs, Organisation Parents and
Organisations in order to be useful. To have a fully functional site, you'll
also want some reviews and of course, some problems.

The best way to do this is to take an anonymised dump of what's on the current
live site. We have a command to do this for the organisations/ccgs/parents and
reviews. By doing this you can mostly match the live site,
but don't have to worry about having any real email addresses or private data
in your instance.

As problems are all about private data, and there aren't that many problems on
the live site anyway, it's better to generate some dummy problems than dump
and anonymise them. We have another command which will do just that,
generating randomised problems for all the current orgs from a few "seeds".

To do all that:

### On the live site, dump the current orgs/ccgs/parent and reviews:
    ./manage.py dump_anonymised_data > /tmp/some-file.json

### On your site, load this dump in:
    ./manage.py loaddata /where/you/put/the-file.json

### Add a basic complement of users in the various roles:
    ./manage.py loaddata organisations/fixtures/development_users.json

### Assign appropriate users you just added to the ccgs/parents:
    ./manage.py assign_orgs_to_dev_users

### Generate some dummy problems for the organisations
    ./manage.py create_example_problems 500
You can swap 500 for any number of problems you like, though it'll take longer
to run if you pick a higher number, obviously.

### If you ever need to reload the data, you can run
    ./manage.py flush
    ./manage.py migrate --fake
(Because you just flushed South's records of what was migrated, but the structure is still the same)
Then you can re-run all of the above.

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

To get ChromeDriver, download the appropriate zip directly from: http://chromedriver.storage.googleapis.com/index.html and put the binary somewhere on your $PATH.

After installing them, start Xvfb with:

    Xvfb :99 -ac &

And export your display variable:

    export DISPLAY=:99

You might want to make that happen at every startup with the appropriates
lines in `/etc/rc.local` and `~/.bashrc`

Alternatively, if you don't want to run the selenium tests, set SKIP_BROWSER_TESTS to true in your environment.
