update:
	find . -name '*.pyc' -delete
	pip install -r requirements.txt
	bundle install --path ../gems --binstubs ../gem-bin
	./manage.py syncdb
	./manage.py migrate

dev-data: update
	./manage.py loaddata demo_ccg.json
	./manage.py loaddata demo_organisation_parent.json
	./manage.py loaddata phase_2_organisations.json
	./manage.py loaddata example_problems.json

.PHONY: update dev-data
