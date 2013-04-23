all: css

css:
	sass --version
	sass --style compact web/sass/default.scss web/css/default.css

PHONY: css
