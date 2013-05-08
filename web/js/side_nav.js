;(function($, window) {
    /**
     * SideNavView fixes the sidebar to the top of the window when scrolling.
     *
     * @param {Element} el The element to attach to
     */
    function SideNavView(el) {
        this.el = el;
        this.fixed = false;
        el.find('a').on('click', $.proxy(this.clickHandler, this));
        $(window).on('scroll', $.proxy(this.scrollSpy, this));
    }

    /**
     * Adds .active to a nav item when clicked.
     *
     * @param {Event} e
     */
    SideNavView.prototype.clickHandler = function(e) {
        this.el.find('li.active').removeClass('active');
        $(e.target).closest('li').addClass('active');
    };

    /**
     * Check if the side nav has scrolled to the top of the window, if it
     * has then add .fixed class to it.
     */
    SideNavView.prototype.scrollSpy = function() {
        if ($(window).scrollTop() >= this.topOffset()) {
            this.scrollEnter();
        } else {
            this.scrollLeave();
        }
    };

    /**
     * Fired when the element get to the top of the document.
     */
    SideNavView.prototype.scrollEnter = function() {
        if (this.fixed) { return; }
        this.el.addClass('fixed');
        this.fixed = true;
    };

    /**
     * Fired when the element leaves the top of the document.
     */
    SideNavView.prototype.scrollLeave = function() {
        if (!this.fixed) { return; }
        this.el.removeClass('fixed');
        this.fixed = false;
    };

    /**
     * Get the top offset of the parent of the side nav.
     *
     * @return {Number} The offset of the elements parent.
     */
    SideNavView.prototype.topOffset = function() {
        return this.el.parent().offset().top;
    };

    window.SideNavView = SideNavView;
})(window.jQuery, window);
