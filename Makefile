.PHONY: build-local build-local-no-cache run-local build-selenium \
        run-selenium reqs-install reqs-install-dev generate \
        generate-requirements migrate collectstatic \
        unit-test integration-test

build-local build-local-no-cache run-local build-selenium migrate collectstatic:
	$(MAKE) -C ops/containers $@

run-selenium:
	$(MAKE) -C ops/containers run-selenium-target-local

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
