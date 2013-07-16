// A jQuery plugin to get queryString parameters from a url
(function($, window) {
    $.QueryString = function(a) {
        a = a.split('&');
        if (a === "") return {};
        var b = {};
        for (var i = 0; i < a.length; ++i)
        {
            var p=a[i].split('=');
            if (p.length != 2) continue;
            b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
        }
        return b;
    };
})(window.jQuery, window);

// Our code
(function($){

    var problemsColumns = ['week', 'four_weeks', 'six_months', 'all_time'];
    var problemsHeaderID = 'problems-intervals-header';
    var reviewsColumns = ['reviews_week', 'reviews_four_weeks', 'reviews_six_months', 'reviews_all_time'];
    var reviewsHeaderID = 'reviews-intervals-header';

    // Helper function to toggle which columns are visible in a group
    // of intervals
    var toggleColumns = function(columns, selected) {
        $.each(columns, function(index, columnName) {
            if(columnName === selected) {
                $("td." + columnName).show();
            }
            else {
                $("td." + columnName).hide();
            }
        });
    };

    // Initialise the columns which get javascripted up
    var initialiseColumns = function(columns, filtersTemplate, selectedColumn, headerID) {
        // Get the filter html from an underscore template
        var filters = _.template(
            filtersTemplate,
            {
                selectedColumn: selectedColumn
            }
        );

        // Hide the appropriate columns and their headers
        toggleColumns(columns, selectedColumn);

        // Re-adjust the colspan on the main header for these columns
        $("#" + headerID).attr('colspan', 1).addClass("two-twelfths");

        // Replace all but one sub-header with a select
        $.each(columns, function(index, columnName) {
            if(columnName !== selectedColumn) {
                $(".summary-table__subhead th." + columnName).hide();
            }
        });
        $(".summary-table__subhead th." + selectedColumn)
            .html(filters)
            .addClass('filters__dropdown-wrap');
    };

    // Update all the header links which provide sorts to correctly
    // include the new parameter, so that when a new interval column
    // is selected, it stays selected after someone clicks a sort link
    var updateSortLinks = function(intervalParamName, intervalParamValue, headerID) {
        // Loop over every sort link
        $("th.sortable a").each(function(index, element) {
            // Get the current url
            var $element = $(element);
            var href = $element.attr('href');
            // Turn query string into an object
            var qs = $.QueryString(href.substr(1));
            // Update the existing query string to add or amend the
            // parameter we care about
            qs[intervalParamName] = intervalParamValue;
            // If this link is the header for the interval, update the sort param too
            if($element.parent('th').attr('id') === headerID) {
                qs['sort'] = intervalParamValue;
            }
            // Now turn that into a proper url
            newHref = "?" + $.param(qs);
            // And update the link href
            $element.attr('href', newHref);
        });
    };

    // If we were sorting by an interval field before, and select a different
    // one, we need to reload the page with the sort (including direction)
    // applied to the newly selected column, because there's no way to re-sort
    // things in javascript (because it's a paged table), and otherwise the table
    // will still be sorted by the column we were looking at before
    var checkCurrentSorting = function(qs, columns, intervalParamName, selectedInterval) {
        if(_.has(qs, 'sort')) {
            var sort = (qs['sort'].substr(0,1) === "-") ? qs['sort'].substr(1) : qs['sort'];
            if(_.indexOf(columns, sort) > -1) {
                // We were sorting by an interval column before
                // what direction was the sort?
                var direction = (qs['sort'].substr(0,1) === "-") ? "-" : "";
                var newSort = direction + selectedInterval;
                qs['sort'] = newSort;
                qs[intervalParamName] = selectedInterval;
                window.location.href = "?" + $.param(qs);
            }
        }
    };

    $(function(){
        // Parse the current setup from the query string
        var qs = $.QueryString(window.location.search.substr(1));
        var selectedProblemInterval = 'all_time';
        if (_.has(qs, 'problems_interval')) {
            if (_.indexOf(problemsColumns, qs.problems_interval) > -1) {
                selectedProblemInterval = qs.problems_interval;
            }
        }
        var selectedReviewInterval = 'reviews_all_time';
        if (_.has(qs, 'reviews_interval')) {
            if (_.indexOf(reviewsColumns, qs.reviews_interval) > -1) {
                selectedReviewInterval = qs.reviews_interval;
            }
        }
        // Get the underscore templates
        var problemFiltersTemplate = $("script[name='problems-filters']").html();
        var reviewFiltersTemplate = $("script[name='reviews-filters']").html();

        // Do the inital hiding and turning into a select for the interval columns
        initialiseColumns(problemsColumns,
                          problemFiltersTemplate,
                          selectedProblemInterval,
                          problemsHeaderID);
        initialiseColumns(reviewsColumns,
                          reviewFiltersTemplate,
                          selectedReviewInterval,
                          reviewsHeaderID);

        // Things to do when the selects change
        $("#problems-interval-filters").change(function(e){
            var selected = $(this).val();
            checkCurrentSorting(qs, problemsColumns, "problems_interval", selected);
            toggleColumns(problemsColumns, selected, problemsHeaderID);
            updateSortLinks('problems_interval', selected, problemsHeaderID);

        });
        $("#reviews-interval-filters").change(function(e) {
            var selected = $(this).val();
            checkCurrentSorting(qs, reviewsColumns, "reviews_interval", selected);
            toggleColumns(reviewsColumns, selected, reviewsHeaderID);
            updateSortLinks('reviews_interval', selected, reviewsHeaderID);
        });

        /**
         * Enable select2 on the org name select.
         */
        var $searchBox = $("#search-org-name");

        $searchBox.select2({
            minimumInputLength: 1,
            placeholder: "Search for provider",
            dropdownAutoWidth: true,
            ajax: {
                url: CitizenConnect.base_url + $searchBox.data('search-url'),
                dataType: 'json',
                data: function(term, page) {
                    return {
                        term: term
                    };
                },
                results: function(data, page) {
                    return {results: data};
                }
            }
        });


    });
})(window.jQuery);
