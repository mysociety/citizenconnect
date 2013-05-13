$('button[name="publish"]').on('click', function(e) {
    e.preventDefault();
    $.fancybox({
        autoDimensions: false,
        width: 525,
        height: 'auto',
        content: $('#publish-confirm-modal').html()
    });
});
