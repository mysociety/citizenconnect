#!/bin/bash

# abort on non-zero exit code
set -e

# Get an older postgis versions:
brew tap homebrew/versions
brew install postgis15

POSTGIS_SQL_PATH=/usr/local/share/postgis

# Creating the template spatial database.
createdb -E UTF8 template_postgis
createlang -d template_postgis plpgsql #Adding PLPGSQL language support

# Allows non-superusers the ability to create from this template
psql -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
# Loading the PostGIS SQL routines
psql -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql
psql -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
# Enabling users to alter spatial tables.
psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
