/* Use this script if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'icomoon\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-search' : '&#xe035;',
			'icon-x' : '&#xe000;',
			'icon-checkmark' : '&#xe003;',
			'icon-circle' : '&#xf111;',
			'icon-caret-up' : '&#xf0d8;',
			'icon-caret-down' : '&#xf0d7;',
			'icon-caret-right' : '&#xf0da;',
			'icon-caret-left' : '&#xf0d9;',
			'icon-chevron-right' : '&#xe001;',
			'icon-double-chevron-right' : '&#xe002;',
			'icon-chevron-left' : '&#xe004;',
			'icon-double-chevron-left' : '&#xe005;',
			'icon-warning' : '&#xe006;'
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