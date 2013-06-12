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


dev-data:
	./manage.py loaddata demo_ccg.json
	./manage.py loaddata demo_trust.json
	./manage.py loaddata phase_2_organisations.json
	./manage.py loaddata example_problems.json

PHONY: css watch update dev-data
