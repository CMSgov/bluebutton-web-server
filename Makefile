.PHONY: build-local build-local-no-cache run-local build-selenium \
        run-selenium-local reqs-install reqs-install-dev generate \
        generate-requirements migrate collectstatic \
        unit-test integration-test

build-local build-local-no-cache run-local build-selenium migrate collectstatic run-selenium-local:
	$(MAKE) -C ops/containers $@

reqs-install:
	pip install -r requirements/requirements.txt

reqs-install-dev:
	pip install -r requirements/requirements.dev.txt

generate generate-requirements:
	$(MAKE) -C ops/containers requirements

unit-test:
	pytest -m 'not integration'

integration-test:
	pytest -m 'integration'
