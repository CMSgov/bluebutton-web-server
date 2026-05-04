build-local:
	cd ops/containers ; make build-local ; cd ../..

build-local-no-cache:
	cd ops/containers ; make build-local-no-cache ; cd ../..

run-local:
	cd ops/containers ; make run-local ; cd ../..

exec-web:
	cd ops/containers ; make exec-web ; cd ../..

build-selenium:
	cd ops/containers ; make build-selenium ; cd ../..

run-selenium:
	cd ops/containers ; make run-selenium-local ; cd ../..

reqs-install:
	pip install -r requirements/requirements.txt

reqs-install-dev:
	pip install -r requirements/requirements.dev.txt

generate generate-requirements:
	cd ops/containers ; make requirements ; cd ../..

retrieve-certs:
	cd ops/containers ; make retrieve-certs ; cd ../..

migrate:
	cd ops/containers ;  make migrate ; cd ../..

collectstatic:
	cd ops/containers ; make collectstatic ; cd ../..

unit-test:
	python manage.py test --exclude=integration