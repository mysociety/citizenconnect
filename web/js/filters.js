$(document).ready(function () {

  var organisation_type_selector = 'select[name=organisation_type]';
  var service_selector = 'select[name=service_code], select[name=service_id]';

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

  // Departments are only relevant for hospitals and clinics
  $(organisation_type_selector).change(function() {
    if ($(this).val() === 'hospitals' || $(this).val() === 'clinics'){
      $(service_selector).removeProp('disabled').trigger('update');
    }else{
      $(service_selector).val('').prop('disabled', 'disabled').trigger('update');
    }
  });

  $("select").change(showSelectedFilters);

  // Trigger the change events when the document is ready to set initial values
  $(organisation_type_selector).change();

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
});
