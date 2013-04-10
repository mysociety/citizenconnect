/* Use this script if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span class="i">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-search' : '&#xe000;',
			'icon-x' : '&#xe001;',
			'icon-checkmark' : '&#xe002;',
			'icon-circle' : '&#xe003;',
			'icon-caret-up' : '&#xe004;',
			'icon-caret-down' : '&#xe005;',
			'icon-caret-right' : '&#xe006;',
			'icon-caret-left' : '&#xe007;',
			'icon-chevron-right' : '&#xe008;',
			'icon-double-chevron-right' : '&#xe009;',
			'icon-chevron-left' : '&#xe00a;',
			'icon-double-chevron-left' : '&#xe00b;',
			'icon-warning' : '&#xe00c;',
			'icon-home' : '&#xe00d;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; i < els.length; i += 1) {
		el = els[i];
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};