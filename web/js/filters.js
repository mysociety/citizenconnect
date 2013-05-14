$(document).ready(function () {

  var organisation_type_selector = 'select[name=organisation_type]';
  var service_selector = 'select[name=service_code], select[name=service_id]';

  // Departments are only relevant for hospitals
  $(organisation_type_selector).change(function() {
    if ($(this).val() == 'gppractices'){
      $(service_selector).val('').prop('disabled', 'disabled');
    }else{
      $(service_selector).prop('disabled', false);
    }
  });

  $(service_selector).change(function() {
    if ($(this).val() !== ''){
      $(organisation_type_selector).val('hospitals').prop('disabled', 'disabled');
    }else{
      $(organisation_type_selector).prop('disabled', false);
    }
  });

  // Trigger the change events when the document is ready to set initial values
  $(organisation_type_selector).change();
  $(service_selector).change();

  // Because we disable the fields they won't be sent through,
  // but we set values on them that we want, so we have re-enable them just
  // before the form is submitted
  $('.filters').bind('submit', function() {
    $(this).find('select').removeAttr('disabled');
  });

});
