$(document).ready(function () {

  // Departments are only relevant for hospitals
  // Only GPs belong to CCGs
  $('select[name=organisation_type]').change(function() {
    if ($(this).val() == 'gppractices'){
      $('select[name=service_code]').val('').prop('disabled', 'disabled');
    }else{
      $('select[name=service_code]').prop('disabled', false);
    }
    if ($(this).val() == 'hospitals'){
      $('select[name=ccg]').val('').prop('disabled', 'disabled');
    }else{
      $('select[name=ccg]').prop('disabled', false);
    }
  });

  $('select[name=service]').change(function() {
    if ($(this).val() != ''){
      $('select[name=organisation_type]').val('hospitals').prop('disabled', 'disabled');
    }else{
      $('select[name=organisation_type]').prop('disabled', false);
    }
  });

  $('select[name=ccg]').change(function() {
    if ($(this).val() != ''){
      $('select[name=organisation_type]').val('gppractices').prop('disabled', 'disabled');
      $('select[name=service_code]').val('').prop('disabled', 'disabled');
    }else{
      $('select[name=organisation_type]').prop('disabled', false);
      $('select[name=service_code]').prop('disabled', false);
    }
  });

  // Trigger the change events when the document is ready to set initial values
  $('select[name=ccg]').change();
  $('select[name=organisation_type]').change();
  $('select[name=service_code]').change();

});
