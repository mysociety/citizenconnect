jQuery(function($) {

    /**
    * Enable select2 on the org name select.
    */
    var $searchBox = $("#map-search-org-name");

    $searchBox.select2({
        minimumInputLength: 1,
        placeholder: "Search for an organisation or area",
        ajax: {
            url: $searchBox.data('search-url'),
            dataType: 'json',
            data: function(term, page) {
                return {
                    term: term
                };
            },
            results: function(data, page) {
                return {results:data};
            }
        }
    });

});
