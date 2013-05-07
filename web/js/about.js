;(function(jQuery, window) {
    jQuery(document).ready(function($) {
        var $sideNav = $('.side-nav');
        var sidenavTopOffset = $sideNav.parent().offset().top;
        $(window).on('scroll', function() {
            if ($(window).scrollTop() >= sidenavTopOffset) {
                $sideNav.addClass('fixed');
            } else {
                $sideNav.removeClass('fixed');
            }
        });

        $('a', $sideNav).on('click', function(e) {
            $sideNav.find('li.active').removeClass('active');
            $(this).closest('li').addClass('active');
        });
    });
})(window.jQuery, window);
