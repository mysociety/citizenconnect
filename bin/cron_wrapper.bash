#!/bin/bash

# abort on any errors
set -e

# check that we are in the expected directory
cd `dirname $0`/..
source ../virtualenv-citizenconnect/bin/activate

# don't abort on error so we can capture output
set +e

# run the command
output="`./manage.py $1`"

# suppress output unless we got a non-zero exit status
if [ "$?" -ne 0 ]
then
  echo ""
  echo "### output captured before '$1' exited ###"
  echo ""
  echo "$output"
fi
