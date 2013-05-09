;(function($, window) {
    /**
     * SideNavView fixes the sidebar to the top of the window when scrolling.
     *
     * @param {Element} el The element to attach to
     */
    function SideNavView(el) {
        this.el = el;
        el.find('a').on('click', $.proxy(this.clickHandler, this));
        el.scrollspy({
            min: this.topOffset(),
            onEnter: $.proxy(this.scrollEnter, this),
            onLeave: $.proxy(this.scrollLeave, this)
        });
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
     * Fired when the element get to the top of the document.
     */
    SideNavView.prototype.scrollEnter = function() {
        this.el.addClass('fixed');
    };

    /**
     * Fired when the element leaves the top of the document.
     */
    SideNavView.prototype.scrollLeave = function() {
        this.el.removeClass('fixed');
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
