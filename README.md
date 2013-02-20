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

### Gather all the static files in one place
    ./manage.py collectstatic --noinput

API
---

### API urls:

`https://citizenconnect.staging.mysociety.org/api/v0.1/problem`
`https://citizenconnect.staging.mysociety.org/api/v0.1/question`

### Posting to the API

The api accepts the following fields and values:

`organisation` - Required.

The ODS Code of an organisation, an example you can use is:
- `RN542` (Andover War Memorial Hospital)

`service_code` - Optional.

The service code of a department, only available for hospitals, for RN542 you can use:
- `SRV0062` (Minor Injuries Unit)

`description` - Required.

The text of the problem or question.

`category` - Required.

The problem or question category, these are still being decided, but currently we have:

For problems: `cleanliness`, `staff`, `appointments`, `other`
For questions: `services`, `prescriptions`, `general`

`reporter_name` - Required.

The reporter of the problem/question's name.

`reporter_email` - Optional, but one of `reporter_email` or `reporter_phone` is required.

The reporter's email address.

`reporter_phone` - Optional, but one of `reporter_email` or `reporter_phone` is required.

`public` - Required

Whether or not the reporter wanted the problem/question made public, send `0` or `1` for true or false.

`public_reporter_name` - Required

Whether or not the reporter wanted their name made public, send `0` or `1` for true or false

`preferred_contact_method` - Required

The reporter's preferred contact method, the available options are: `phone`, `email`

`source` - Required

The source of the original report, ie: whether they phoned, emailed or texted. Available options: `email`, `phone`, `sms`

###Return value
The api returns a json string, containing an object with one parameter, `reference_number` which gives the unique reference number for the problem or question created (if successful).

Example:

```javascript
{
    "reference_number":"Q3"
}
```

### Errors
The api returns a json string for errors too, with all errors being contained inside a parameter `errors`. Inside `errors`, the errors are arrays of string error messages, keyed by the field name to which the error pertains, or `__all__` if it's not specific to a field.

Example (from sending an empty body):

```javascript
{
    "errors":
    {
            "category": ["This field is required."],
            "description": ["This field is required."],
            "__all__": ["You must provide either a phone number or an email address."],
            "organisation": ["This field is required."],
            "source": ["This field is required."],
            "preferred_contact_method": ["This field is required."]
    }
}
```

The above example shows only one error for each field, and one for `__all__`, there could be more.

### Testing that it worked
For now the easiest way to see if it worked (besides the `reference_number` being returned) is to go to the dashboard page for the organisation and seeing it it's displayed there. For the organisation given, this would be: https://citizenconnect.staging.mysociety.org/private/dashboard/RN542