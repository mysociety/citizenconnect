;(function(jQuery, window) {
    /**
     * SideNavView fixes the sidebar to the top of the window when scrolling.
     *
     * @param {Element} el The element to attach to
     */
    function SideNavView(el) {
        this.el = el;
        el.find('a').on('click', $.proxy(this.addActiveClass, this));
        $(window).on('scroll', $.proxy(this.checkOffset, this));
    }

    /**
     * Adds .active to a nav item when clicked.
     *
     * @param {Event} e
     */
    SideNavView.prototype.addActiveClass = function(e) {
        this.el.find('li.active').removeClass('active');
        $(e.target).closest('li').addClass('active');
    }

    /**
     * Check if the side nav has scrolled to the top of the window, if it
     * has then add .fixed class to it.
     */
    SideNavView.prototype.checkOffset = function() {
        if ($(window).scrollTop() >= this.topOffset()) {
            this.el.addClass('fixed');
        } else {
            this.el.removeClass('fixed');
        }
    }

    /**
     * Get the top offset of the parent of the side nav.
     *
     * @return {Number} The offset of the elements parent.
     */
    SideNavView.prototype.topOffset = function() {
        return this.el.parent().offset().top;
    }

    window.SideNavView = SideNavView;
})(window.jQuery, window);
