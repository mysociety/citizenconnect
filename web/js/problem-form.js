;(function($, priorityCategories){

    var descriptionLimit = 2000;

    var showDescriptionCount = function($descriptionCount, $description, $descriptionErrors) {
        var left = descriptionLimit - $description.val().length;
        // We want to show negative counts in red
        if (left < 0) {
            $descriptionCount.html('<span class="icon-warning"></span> Characters left: ' + left).addClass('error');
            // also show a proper error and disable the submit button
            $descriptionErrors.html(renderError("Please limit your description to 2000 characters."));
            $(".problem-form button[type=submit]").prop('disabled', 'disabled').addClass('btn--disabled');
        }
        else {
            $descriptionCount.html('<span class="icon-checkmark"></span> Characters left: ' + left).removeClass('error');
            if(typeof $descriptionErrors !== 'undefined') {
                $descriptionErrors.empty();
            }
            $(".problem-form button[type=submit]").prop('disabled', false).removeClass('btn--disabled');
        }
    };

    var renderError = function(error) {
        return '<ul class="message-list"><li class="message-list__error">' + error + '</li></ul>';
    };

    $(function() {
        // Big radio buttons
        $('.big-radio-group').each(function(){
            var $t = $(this);

            // add dummy radio element
            $('input[type=radio]', $t).each(function(){
                $(this).hide().after('<div class="big-radio-group__cell"><div class="big-radio-group__radio"></div></div>');
            });

            // bind the click event so we can update the actual inputs
            $('li', $t).on('click', function(){
                $('li', $t).removeClass('big-radio-group--active');
                $('input[type=radio]', $(this)).prop("checked", true);
                $(this).addClass('big-radio-group--active');
            });
        });
        
        // Find the checked radio button and trigger the click
        $('.big-radio-group input[type=radio]').each(function(){
            if($(this).is(':checked')){
                $(this).parents('li').click();
            }
        });
        

        // Category fields
        $('input[name="category"]').change(function () {
            var val = $(this).val();

            var $input = $('#id_elevate_priority');
            var $containting_element = $input.parents('ul');

            if ( priorityCategories[val] ) {
                $containting_element.show();
            } else {
                $containting_element.hide();
            }
        });

        $('input[name="category"]:checked').change();

        // Problem description
        var $description = $("#id_description");
        var $descriptionCount = $('.description-count');
        var $descriptionErrors = $(".description-errors");
        showDescriptionCount($descriptionCount, $description);

        // Count down the available text when things change
        $description.on("propertychange input textInput", function () {
            showDescriptionCount($descriptionCount, $description, $descriptionErrors);
        });

        // Check length before submitting
        $(".problem-form").submit(function(){
            if($description.val().length > descriptionLimit) {
                // TODO - show an error message
                window.alert("Sorry, your message is too large");
                return false;
            }
        });

        var $serviceSelect = $('#id_service');
        var $servicePlaceholder = $serviceSelect.find('option:first').remove();
        $serviceSelect.prepend('<option></option>');
        $serviceSelect.val(''); // select the empty value, so placeholder text shown.
        $serviceSelect.select2({
            placeholder: $servicePlaceholder.text(),
            allowClear: true
        });
    });


})(window.jQuery, window.CitizenConnect.priorityCategories);


/*
  If the "under 16" box is ticked we should hide the "all public" option and
  if it was ticked select the "private" option.
*/
$(function () {
  var $private_checkbox = $('#id_privacy_0');
  var $publish_with_name_box = $($('#id_privacy_2').parents('li').get(0));
  $('input[name="reporter_under_16"]').click(function () {
      var $ele = $(this);
      if ($ele.is(':checked')) {
        if ($publish_with_name_box.find('input').is(':checked')) {
          $private_checkbox.click();
        }
        $publish_with_name_box.hide();
      } else {
        $publish_with_name_box.show();
      }
   });
});
