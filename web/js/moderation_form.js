jQuery(document).ready(function($) {
    $('button[name="publish"]').on('click', function(e) {
        e.preventDefault();

        var $content = $('#publish-confirm-modal').clone();

        var moderatedDescription = $('#id_moderated_description').val();
        if (moderatedDescription && moderatedDescription !== "") {
            $('.content', $content).html('<p>' + moderatedDescription + '</p>');
        }


        var $nameMessage = $('.content-name', $content);
        var publishNameBool = $('#id_public_reporter_name').is(':checked') || false;
        if (publishNameBool) {
          $nameMessage.html('Name "<strong>' + $nameMessage.data('reporterName') + '</strong>" will  be published');
        } else {
          $nameMessage.html('Name will <strong>not</strong> be published');
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

    var mightDisablePublishButton = function(e) {
        if ($(this).val() == 7) {
            $('button[name="publish"]').attr('disabled', 'disabled');
        }
    };

    $('#id_status').on('change', mightDisablePublishButton);
});
