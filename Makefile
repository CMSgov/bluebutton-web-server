reqs-compile:
	pip-compile --output-file requirements/requirements.txt requirements/requirements.in

reqs-download:
	pip download -r requirements/requirements.txt --dest vendor --platform linux_x86_64 --no-deps

reqs-install:
	pip install -r requirements/requirements.txt --no-index --find-links ./vendor/
