# Notes on the NHS Choices API


These notes are based on email responses from the NHS to questions, and on observed behaviour. The API is under development, so it is likely that some of these notes will be wrong.

These notes also focus on reading out reviews, and detecting take-downs.


## Documentation

Formal documentation for the API is in a PDF at http://blogs.nhs.uk/choices-blog/files/2013/05/NHS-Choices-API-documentation.pdf

There is also some introductory blurb at http://www.nhs.uk/aboutNHSChoices/professionals/syndication/Pages/Webservices.aspx

In several places the observed behaviour differs from the documentation. The syndication team has been queried about it. In particular for GP ratings for certain questions the wording associated with a score does not match the meaning of the score.


## Auth

Add an `apikey` query parameter to all requests.


## API structure

The API is loosely RESTful but frequently departs from the concept of collections and documents.

It is intended that you can navigate it in a browser using HTML and then change the urls to get the response format desired. Many of the provided forms for creating urls are broken though, and not all endpoints have HTML equivalents.


## Endpoints

For all comments for an organisation type, with `:org_type` being something like `hospitals`:

`/organisations/:org_type/comments`

For comments changed since a certain date (not including ones that are no longer included in the API as they are over two years old):

`/organisations/:org_type/commentssince/:year/:month/:day`


## Ordering

The reviews are in created order, but the created timestamp is not exposed in the API. Prior to querying it was believed by the NHS team that they were in `published` order. Note that the meaning of the `published` and `updated` timestamps is uncertain as they are both reset at certain times - eg when marking a review for takedown.

It is not possible to change the ordering.


## Formats

If no suffix like `.atom` is added then the response depends on your request's `Accept` header. This means that your browser and command line clients will very likely see different content (eg browser sees atom, curl sees RSS).

I've seen atom, rss, html, xml and json be available. However it depends on the endpoint.

For comments the `content` tag is xhtml with divs for sections called `liked`, `improved`, `anythingElse` and `commentTags`. For replies the `content` tag contains just text.


## Filtering

Filtering is done using the `commentssince` form of the path. It does not appear to be possible to filter using query parameters.


## IDs

For the reviews IDs appear to sequential integers although many are not seen presumably because they are moderated out before reaching the API. Replies have the id of the comment they refer to with an `R` appended.


## Missing data

For reviews the `visit_date` (which should be of the form of month and year of visit) is missing.


## Erroneous data

Review titles are sometimes double escaped: `A&E on a Saturday` vs `A&amp;E and Eye Clinic.`. This is not being corrected atm in our code.

For ratings the score and answer wording of the Friends and Family questions appears have been reversed in some cases (glowing reviews and high ratings will have a very negative F&F rating).


## Empty responses

These come back as `404`s - not empty lists (have confirmed that this is the intended behaviour, have queried whether it is the correct behaviour).


## Detecting change reviews

It has been confirmed by email that "Any comment that is changed (be it content or category) will appear in the 'commentssince' results and so this is the only one we need to query to stay up to date" is correct and so we do not need to do intermittent polls of all previous comments.
