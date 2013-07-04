# Care Connect API Preliminary Documentation

## API url

```
https://citizenconnect.staging.mysociety.org/api/v0.1/problem
```

## Posting to the API
The api accepts the following fields and values:

### organisation
Required for problems. The ODS Code of an organisation, an example you can use is: `RN542` (Andover War Memorial Hospital). Optional for questions.

### service_code
Optional. The service code of a department, only available for hospitals, for `RN542` you can use: `SRV0062` (Minor Injuries Unit) Ignored for questions

### commissioned
Required. Whether the service is commissioned locally or nationally. Use `0` or `1` for locally or nationally commissioned.

### description
Required. The original text of the problem or question. Limited to a maximum of 2000 characters.

### moderated_description
Required for public problems that are to be published (see `public` and `publication_status` below). A moderated description of the problem or question, suitable for publication. No character limit applied.

### category
Required. The problem or question category, currently we have:
For both questions and  problems: [`staff`, `access`, `delays`, `treatment`, `communication`, `cleanliness`, `equipment`, `medicines`, `dignity`, `parking`, `lostproperty`, `food`, `other`]

### breach
Optional. Whether the problem constitutes a breach of standards. Send `0` or `1` for false or true. Defaults to false.

### priority
Optional. Whether the problem is a priority (user is asked 'is this happening right now'). Invalid for the following categories [equipment, parking, lostproperty, other]. Send `20` for normal priority, `50` for high priority, defaults to normal priority.

### requires_second_tier_moderation
Optional. Whether the problem requires second tier moderation. Send `0` or `1` for false or true. Defaults to false.

If true then the `publication_status` of the problem will be set to `NOT_MODERATED` rather than the default of `PUBLISHED`.

### reporter_name
Required. The reporter of the problem/question's name.

### reporter_email
Mandatory. The reporter's email address.

### reporter_phone
Optional. The reporter's phone number.

### public
Optional. Whether or not the reporter wanted the problem/question made public, send `0` or `1` for false or true. Defaults to false.

### public_reporter_name
Optional. Whether or not the reporter wanted their name made public, send `0` or `1` for false or true. Defaults to false

### preferred_contact_method
Optional. The reporter's preferred contact method, the available options are: `phone`, `email`. Defaults to `email`.

### source
Required. The source of the original report, ie: whether they phoned, emailed, texted etc. Available options: [`email`, `phone`, `sms`, `twitter`, `facebook`, `mms`]

### escalated
Optional. Whether or not this problem has been escalated. Send `0` or `1` for true or false. Defaults to false.

## Return value
The api returns a json string, containing an object with one parameter, reference_number which gives the unique reference number for the problem or question created (if successful). Example:

``` JSON
    {
        "reference_number":"P3"
    }
```

## Errors
The api returns a json string for errors too, with all errors being contained inside a parameter `errors`. Inside `errors`, the errors are arrays of string error messages, keyed by the field name to which the error pertains, or `__all__` if it's not specific to a field. Example (from sending an empty body):

``` JSON
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

**Note:** The above example shows only one error for each field, and one for `__all__`, there could be more.

## Testing that it worked
For now the easiest way to see if it worked (besides the reference_number being returned) is to go to the dashboard page for the organisation and seeing it it's displayed there. For the organisation given, this would be: https://citizenconnect.staging.mysociety.org/private/dashboard/RN542
