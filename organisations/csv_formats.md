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

## Trust users

- `Username`
- `Email`
- `Code`: The ODS code for the trust.

## CCG users

- `Username`
- `Email`
- `Code`: The CCG code

# Representing Null values

Ideally leave the field blank, or for some fields the value `NULL` can be used.
This appears to be needed in some cases where the spreadsheet software does not
handle empty fields well when producing CSV files.
