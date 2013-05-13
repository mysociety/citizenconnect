# Notes on the NHS Choices API

The API does not appear to have any formal documentation. These notes are
based on email responses from the NHS to questions, and on observed behavior.
The API is under development, so it is likely that some of this will be wrong.

These notes also focus on reading out reviews, and detecting take-downs.


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

The comments should always be in published order, but observation of the API shows that they are in created order, but the created timestamp is not exposed in the API. Note that the meaning of the `published` and `updated` timestamps is uncertain as they are both reset at certain times - eg when marking a review for takedown.

It is not possible to change the ordering.


## Formats

If no suffix like `.atom` is added then the response depends on your request's `Accept` header. This means that your browser and command line clients will very likely see different content (eg browser sees atom, curl sees RSS).

I've seen atom, rss, html, xml and json be available. However it depends on the endpoint.


## Filtering

Filtering is done using the `commentssince` form of the path. It does not appear to be possible to filter using query parameters.


## IDs

For the reviews IDs appear to sequential integers although many are not seen presumably because they are moderated out before reaching the API. Replies have the id of the comment they refer to with an `R` appended.


## Missing data

For reviews the `visit_date` (which should be of the form of month and year of visit) is missing.

For ratings the score and answer wording of the Friends and Family questions appears have been reversed in some cases (glowing reviews and high ratings will have a very negative F&F rating).


## Empty responses

These come back as `404`s - not empty lists (have queried if this is the intended behaviour).
