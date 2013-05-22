// This javascript function should be included before the rateit plugin so
// that it can fix up the option values before that plugin sees them.


// This JS does two things - it goes through all the selects and changes the
// values of the options to be 0, 1, ... in order. It stores the original
// values in the data part. This is done so that the rateit plugin correctly
// interprets the value as the corresponding star value, rather than the id of
// the answer selected.

// It then traps the form submit and restores the original values to the
// options so that the values posted are what the server expects.

$(function () {

    $('div.review-form__rating-answer select').each(function() {
        var score = 0;
        var $select = $(this);
        $select.find('option').each(function () {
            var $option = $(this);
            $option.data('originalValue', $option.val());
            $option.val(score);
            score += 1;
        });

        // For the selenium testing put the name of the select on the enclosing div
        $select.parent('div').attr('data-select-name', $select.attr('name'));
    });

    $("div.review-form form").submit(function (submitEvent) {
        var $form = $(this);
        $('div.review-form__rating-answer option').each(function() {
            var $option = $(this);
            $option.val($option.data('originalValue'));
        });
        return true;
    });

    // Add a tooltip when hovering over the stars.
    $(".rateit").bind('over', function (event,value) {
        var $rating_element = $(this);
        var $select = $rating_element.siblings('select');
        var $option = $select.find('option[value="' + value + '"]');
        $rating_element.attr('title', $option.text());
    });

});
