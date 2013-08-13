$(document).ready(function () {

  var organisation_type_selector = 'select[name=organisation_type]';
  var service_selector = 'select[name=service_code], select[name=service_id]';

  // Function to enable/disable the services filter depending on
  // the value of the organisation type filter
  var setUpServiceFilter = function() {
    var org_type_value = $(organisation_type_selector).val();
    if (org_type_value === 'hospitals' || org_type_value === 'clinics') {
      $(service_selector).prop('disabled', false).trigger('update');
    } else {
      $(service_selector).val('').prop('disabled', true).trigger('update');
    }
  };

  // Function to add in some html to show the selected filters
  var showSelectedFilters = function() {
      $(".filters select").each(function(index, element) {
          var $select = $(element);
          var $dropdown = $select.parent('.filters__dropdown');
          if($select.val() !== "" && !$select.prop('disabled')) {
              $dropdown.removeClass('filters__dropdown--default');
          }
          else {
              $dropdown.addClass('filters__dropdown--default');
          }
      });
  };

  // Bind change events
  $("select").change(function() {
    $(".filters").trigger("CitizenConnect.filters.update");
  });

  $(".filters").on("CitizenConnect.filters.update", function() {
    setUpServiceFilter();
    showSelectedFilters();
  });

  // Because we disable the fields they won't be sent through,
  // but we set values on them that we want, so we have re-enable them just
  // before the form is submitted
  $('.filters').bind('submit', function() {
    $(this).find('select').removeProp('disabled');
  });

  // Makes styling select elements work cross-browser.
  if (!$('html').hasClass('ie7')) {
    $('.filters__dropdown select').customSelect();
  }

  // Manually update the filters once everything is in place
  $(".filters").trigger("CitizenConnect.filters.update");
});
