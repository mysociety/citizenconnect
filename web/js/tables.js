(function($, window){
    $(function(){
        // Make clicking on table rows go to their link
        $("tr.table-link__row").on('click', function(e) {
            var href = $(e.target).closest("tr").attr('data-href');
            // Review links should open in a new tab
            if ($('body').hasClass('org-parent-reviews')) {
                var win = window.open(href, '_blank');
                win.focus();
            } else {
                window.location = href;
            }
        });
    });
})(window.jQuery, window);
