#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..
source ../virtualenv-citizenconnect/bin/activate

./manage.py email_surveys_to_reporters
