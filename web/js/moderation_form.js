jQuery(document).ready(function($) {
    $('button[name="publish"]').on('click', function(e) {
        e.preventDefault();
        var $content = $('#publish-confirm-modal').clone();
        var moderatedDescription = $('#id_moderated_description').val();
        if (moderatedDescription && moderatedDescription !== "") {
            $('.content', $content).html('<p>' + moderatedDescription + '</p>');
        }
        $.fancybox({
            autoDimensions: false,
            width: 525,
            height: 'auto',
            content: $content.html()
        });
    });

    $('body').on('click', '.cancel', function(e) {
        e.preventDefault();
        $.fancybox.close();
    });

    $('body').on('click', '.publish', function(e) {
        $('button[name="publish"]').off('click').trigger('click');
        e.preventDefault();
    });
});
