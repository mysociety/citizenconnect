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
- `CCG Code`: The ODS code of the CCG (will be used for `escalation_ccg`, and for CCG memberships_)
- `Email`

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
- `Email`:
