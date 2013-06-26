# Geocoder

This is a Django app that lets you load Ordnance Survey data and use it to find places. It was written for the NHS [Citizen Connect](https://github.com/mysociety/citizenconnect) project.


## Data

http://www.ordnancesurvey.co.uk/oswebsite/products/os-opendata.html

The Ordnance Survey make large data sets available under an open license. See the url above for more details. This app uses the OS Locator and 1:50k Gazetteer.


## Importing data

- Download the data from the Ordnance Survey website.
- Set the `GEOCODER_BOUNDING_BOXES` entry in your `settings.py`.
- Import the data using one of the import management commands, the path to the data file is the only argument.


## Licensing

Anywhere you make use of the data from the OS you should display the following text:

> Contains Ordnance Survey data © Crown copyright and database right 2013

See the [OS OpenData Licensing](http://www.ordnancesurvey.co.uk/oswebsite/opendata/licensing.html) page for more details.
