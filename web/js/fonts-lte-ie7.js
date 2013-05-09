/* Load this script using conditional IE comments if you need to support IE 7 and IE 6. */

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
			'icon-home' : '&#xe00d;',
			'icon-stack' : '&#xe00f;',
			'icon-calendar' : '&#xe010;',
			'icon-arrow-up-right' : '&#xe011;',
			'icon-star' : '&#xe013;',
			'icon-star-2' : '&#xe012;',
			'icon-tag' : '&#xe015;',
			'icon-user' : '&#xe00e;',
			'icon-star-3' : '&#xe014;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; ; i += 1) {
		el = els[i];
		if(!el) {
			break;
		}
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