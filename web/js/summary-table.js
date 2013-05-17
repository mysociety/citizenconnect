// A jQuery plugin to get queryString parameters
(function($, window) {
    $.QueryString = (function(a) {
        if (a === "") return {};
        var b = {};
        for (var i = 0; i < a.length; ++i)
        {
            var p=a[i].split('=');
            if (p.length != 2) continue;
            b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
        }
        return b;
    })(window.location.search.substr(1).split('&'));
})(window.jQuery, window);

// Our code
(function($){

    var problemsColumns = ['week', 'four_weeks', 'six_months', 'all_time'];
    var problemsHeaderID = 'problems-intervals-header';
    var reviewsColumns = ['reviews_week', 'reviews_four_weeks', 'reviews_six_months', 'reviews_all_time'];
    var reviewsHeaderID = 'reviews-intervals-header';

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

    var initialiseColumns = function(columns, filtersTemplate, selectedColumn, headerID) {
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

    $(function(){

        var qs = $.QueryString;
        var selectedProblemInterval = (qs.hasOwnProperty('problems_interval')) ? qs['problems_interval'] : 'all_time';
        var selectedReviewInterval = (qs.hasOwnProperty('reviews_interval')) ? qs['reviews_interval'] : 'reviews_all_time';
        var problemFiltersTemplate = $("script[name=problems-filters]").text();
        var reviewFiltersTemplate = $("script[name=reviews-filters]").text();

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
            toggleColumns(problemsColumns, selected, problemsHeaderID);
        });

        $("#reviews-interval-filters").change(function(e) {
            var selected = $(this).val();
            toggleColumns(reviewsColumns, selected, reviewsHeaderID);
        });
    });
})(window.jQuery);