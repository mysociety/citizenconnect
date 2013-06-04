all: css

SASS = sass
STYLE = compact
SOURCE = web/sass/default.scss
TARGET =  web/css/default.css

css:
	$(SASS) --version
	$(SASS) --style $(STYLE) $(SOURCE) $(TARGET)

watch:
	$(SASS) --watch --style $(STYLE) $(SOURCE):$(TARGET)

update:
	find . -name '*.pyc' -delete
	pip install -r requirements.txt
	./manage.py syncdb
	./manage.py migrate

PHONY: css watch update
