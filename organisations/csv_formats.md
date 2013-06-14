# Formatting of CSV files for data boot strapping

There are several management commands that will read in CSV files to set up the
CCGs, trusts and organisations.

They all expect CSV with the first row being the a header row describing the
contents of each column. These are the headers expected (they are case
sensitive):

## CCGs

- `ODS Code`: The ODS code
- `Name`
- `Region`: A geographic region, eg "London"
- `Email`

## Trusts

- `ODS Code`: The ODS code of the trust
- `Name`
- `Escalation CCG`: The ODS code of the escalation CCG. This CCG will also be added to the CCGs that this trust belongs to.
- `Other CCGs`: The ODS codes (separated by a `|` if more than one) of CCGs that this trust belongs to, in addition to the `Escalation CCG`. May be blank.
- `Email`
- `Secondary Email`

## Organisations

- `ODS Code`: The ODS code for this org
- `ChoicesID`: The Choices ID of this org
- `Name`
- `Trust Code`: The ODS code of the Trust (should match that provided in the trusts CSV)
- `OrganisationTypeID`: What is this org. Eg `HOS`
- `URL`
- `Address1`
- `Address2`
- `Address3`
- `City`
- `County`
- `Latitude`
- `Longitude`
- `LastUpdatedDate`
- `Postcode`
- `ServiceCode`
- `ServiceName`

## Trust and CCG users

Users for the trusts and CCGs should be listed in separate CSV files (one for trusts, one for CCGs). If a user belongs to several trusts or CCGs there should be multiple entries in the CSV, one per organisation that they belong to.

If the users do not exist they are created and an intro email sent, if the do exist their membership is confirmed. Note that deleting a user from the CSV will **not** delete them from the organisation.

- `Username`
- `Email`
- `Code`: The ODS code for the trust or CCG.


# Representing Null values

Ideally leave the field blank, or for some fields the value `NULL` can be used.
This appears to be needed in some cases where the spreadsheet software does not
handle empty fields well when producing CSV files.
