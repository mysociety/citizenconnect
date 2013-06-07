(function($, window){
    $(function(){
        // Make clicking on table rows go to their link
        $("tr.table-link__row").click(function(e) {
            var href = $(e.target).closest("tr").attr('data-href');
            window.location = href;
        });
    });
})(window.jQuery, window);
