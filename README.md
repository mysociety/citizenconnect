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
Assuming you're on a debian/ubuntu server:
    sudo xargs -a conf/packages apt-get install

### Create a postgres database and user
    sudo -u postgres psql
    postgres=### CREATE USER citizenconnect WITH password 'citizenconnect';
    CREATE ROLE
    postgres=### CREATE DATABASE citizenconnect WITH OWNER citizenconnect;
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

### Gather all the static files in one place
    ./manage.py collectstatic --noinput