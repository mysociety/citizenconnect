# Overview

A website for the NHS to allow people to report problems about their GP, Hospital, Clinic, etc.

The basic idea is quite similar to FixMyStreet - find something to report a problem about, and then fill in a form to report it to the right person. The main addition to this model is that as well as something being emailed to the people responsible, they also have a section of the site to login, see their open problems, and respond to them. In addition, there's a moderation process where problems are checked for suitability (non-medical, not personally identifiable, etc) before they are shown in full to the public.

There are a series of pages allowing people to see an overview of what problems there are, both geographically on a map, and in tabular form. This information can be "drilled-down" to see summaries of individual organisations, their problems, reviews and so on.

There's also functionality for people to leave reviews and star ratings of GP's, Hospitals, etc, in a similar way to what's possible on the NHS Choices site.

The site is loaded with data provided by the NHS about what organisations and services exist, as well as Ordnance Survey data about road/place names, and it uses MapIt data to perform postcode lookups.

In addition, the site regularly extracts data from NHS Choices' API about the overall ratings of organisations, and the reviews they have received on other sites.
