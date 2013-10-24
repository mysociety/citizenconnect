/**
 * Enable select2 on the org name select.
 */
(function($) {
    $(function() {
        $("#id_organisation").select2({
            minimumInputLength: 1,
            placeholder: "Search for provider",
            dropdownAutoWidth: true,
            allowClear: true
        });
    });
})(window.jQuery);
