reqs-compile:
	pip-compile --generate-hashes --output-file requirements/requirements.txt requirements/requirements.in
	pip-compile --generate-hashes --output-file requirements/requirements.dev.txt requirements/requirements.dev.in

# Note: requirements.dev.txt includes packages from requirements.txt also.
reqs-download:
	pip download -r requirements/requirements.dev.txt --dest vendor --platform linux_x86_64 --no-deps

reqs-install:
	pip install --require-hashes -r requirements/requirements.txt --no-index --find-links ./vendor/

reqs-install-dev:
	pip install --require-hashes -r requirements/requirements.dev.txt --no-index --find-links ./vendor/
