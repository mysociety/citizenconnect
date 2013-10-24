/**
 * Enable select2 on the org name select.
 */
(function($) {

    $(function() {

        var $orgSelect = $("#id_organisation");
        var $startDate = $("#id_start");
        var $endDate = $("#id_end");
        var dateFormat= "dd/mm/yyyy";

        // Turn on select2 for the organisation dropdown
        // Before we turn it on we need to massage the content of the options
        // a little, so that select2's placeholder and clearing works correctly
        // because it's expecting a totally empty <option> tag at the top
        $orgSelect.children("option[value='']").replaceWith("<option></option>");
        $orgSelect.select2({
            placeholder: "Search for provider",
            dropdownAutoWidth: true,
            allowClear: true
        });

        // Turn on datepickers for the start and end dates
        $startDate.datepicker({
            format: dateFormat
        });
        $endDate.datepicker({
            format: dateFormat
        });

    });
})(window.jQuery);
