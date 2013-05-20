jQuery(document).ready(function($) {

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

});
