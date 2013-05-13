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
