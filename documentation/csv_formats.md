# Formatting of CSV files for data boot strapping

There are several management commands that will read in CSV files to set up the
CCGs, trusts and organisations.

They all expect CSV with the first row being the a header row describing the
contents of each column. These are the headers expected (they are case
sensitive):

## Sample files

There are several sample csv files in the [documentation/csv_samples folder](https://github.com/mysociety/citizenconnect/blob/master/documentation/csv_samples). These are used in the test suite so should always be accurate.

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

## Users

Some of these values are "flags" that can be true or false. To set them true use the value `x`, or leave blank for false. If the flag is true then the user will be assigned that status.

Passwords are not specified in this import. For new users a random password is created. They should use the password reset facility to set a new one (reset email will be sent to the address specified in the import).

- `Name`: The username, will be used when logging in.
- `Email`: The email address that password resets etc will be sent to
- `NHS Superusers`: Flag for superuser status
- `Case Handlers`: Flag for case handler status
- `Second Tier Moderators`: Flag for second tier moderator status
- `Customer Contact Centre`: Flag for CCC status

Note that the last row in the sample CSV is deliberately bad, and is there for the test scripts.


# Representing Empty values

Ideally leave the field blank, or for some fields the value `NULL` can be used.
This appears to be needed in some cases where the spreadsheet software does not
handle empty fields well when producing CSV files.
