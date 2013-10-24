/**
 * Enable select2 on the org name select.
 */
(function($) {

    $(function() {

        // Turn on select2 for the organisation dropdown
        var $orgSelect = $("#id_organisation");
        // Before we turn it on we need to massage the content of the options
        // a little, so that select2's placeholder and clearing works correctly
        // because it's expecting a totally empty <option> tag at the top
        $orgSelect.children("option[value='']").replaceWith("<option></option>");
        $orgSelect.select2({
            placeholder: "Search for provider",
            dropdownAutoWidth: true,
            allowClear: true
        });
    });
})(window.jQuery);
