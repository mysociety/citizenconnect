update:
	find . -name '*.pyc' -delete
	pip install -r requirements.txt
	bundle install --path ../gems --binstubs ../gem-bin
	./manage.py syncdb
	./manage.py migrate

.PHONY: update
