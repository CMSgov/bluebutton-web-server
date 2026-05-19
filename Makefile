.PHONY: build-local build-local-no-cache run-local exec-web build-selenium \
        run-selenium reqs-install reqs-install-dev generate \
        generate-requirements retrieve-certs migrate collectstatic \
        unit-test integration-test

# Grouped passthrough targets to ops/containers
build-local build-local-no-cache run-local exec-web build-selenium \
retrieve-certs migrate collectstatic:
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
	python manage.py test --exclude=integration

integration-test:
	python manage.py test --tag=integration