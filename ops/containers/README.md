# containers

The `/ops/container` subtree contains specs for all of Blue Buttons containers. This includes containers that are intended to run in production as well as containerized apps and processes that run local-only.

## tl;dr: local

```bash
make build-local
```

will build all containers needed to stand up Blue Button locally.

```bash
make run-local
```

will run the stack.

## local

Our goal should be for the local application and the production application to be *as similar as possible*. This lets developers be confident that code they develop will behave the same locally as well as in production. 

We can do a few things to try and achieve this:

1. Use the same Dockerfile locally and in production. Some variation may be necessary, but we want things to be "the same as is reasonable."
2. Run the same startup sequence. Our startup scripts (e.g. entrypoint.bash) can contain conditionals if necessary (e.g. is this local vs. production), but if we run the same code in both places, we have more confidence that the conditionals (for example) are right.
3. Provide the same environment. While the local stack will look very different than the containerized Fargate instances, we want the environment provided to the app to look "the same." That means the same environment variables, the same systems (e.g. a mock S3 container), etc.

When we have confidence that our local is "the same" as production, then we have more confidence in the code we write and ship, letting us move faster.

## sequence

To run the local stack, we need to follow a sequence of steps. In production, we have CI/CD. Locally, we have Makefiles. (We could replace these with `act`, but even then, we would be encoding the same steps as the makefiles.)

## build the containers and assets

The first `make` command is a sequence unto itself.

```bash
make build-local
```

expands to

```bash
make requirements
make css
```

followed by commands to build the `mslsx` and `bb-api` containers. This is necessary if you are working on static assets, changing the `requirements.txt` files, or working on MSLS.

## run the stack

Next, you run the stack. You need to be in an active Kion session for this to work.

```bash
make run-local bfd="..." auth="..."
```

where `bfd` is `local`, `test`, or `sbx`, and `auth` is `live` or `mock`. If you do not provide any values, the default is to use `bfd=test auth=live`.

## migrating and collecting static files

If it is the first time you run the stack, you will need to run migrations (in order to initialize the database) and collectstatic (in order to build the CSS assets and move them to the mocked S3 bucket).

First, exec into the web container

```bash
docker exec -it containers-web /bin/bash
```

Then, source the venv that Django is using, and run the migrate and collectstatic management commands.

```bash
source ~/venv/bin/activate
python manage.py migrate
python manage.py collectstatic
```

## structure

Every container should follow this structure as closely as possible.

```md
containers
  | - <application>
  |        | - files (external, internal)
  |        | - scripts (external, internal)
  |        | - Dockerfile
  |        | - Makefile
  | ...
```

The external files are used before running the stack; the internal files are used inside the running container(s), locally and possibly in production.

The Makefile should always have a `build-local` and `run-local` target.

### dockerfile

Each application folder contains a Dockerfile specifying how to build a container that can be run locally or, in some cases, in production.

### makefile

The Makefile always provides two targets:

1. `build-local` for testing in a local stack
2. `build-production` for deployment to cloud environments

### scripts

Scripts external to the container---scripts that configure a local environment, for example---are in `scripts/external`. Scripts that are required inside the container as part of application execution are in `scripts/internal`.

### files

Files necessary to support the application---templates, etc.---are stored here.

## /tmp in the container

We have access to `/tmp` locally and in production. That space is used for writing keys that are passed into the container, as well as templated configuration for services internal to the container.

```md
/tmp
|-- bfd
|   `-- certs
|       |-- cert.pem
|       `-- key.pem
`-- nginx
    |-- certs
    |   |-- cert.pem
    |   `-- key.pem
    |-- nginx.conf
    |-- tmp
    `-- uwsgi_params -> /etc/nginx/uwsgi_params
```

# testing

## unit testing

Unit testing will be ran outside a container.

### prerequisites:

1. Ensure you have python 3.12 installed locally
2. pip install pip==25.3
3. pip install pip-tools setuptools

### running unit tests

Setup your local venv (or whatever flavor of local python environment) and install the dev dependencies

1. Activate your environment
2. Install the requirements into the environment `pip install -r requirements/requirements.dev.txt`
3. Run `python manage.py test --exclude=integration` or `make unit-test`

### debugging - unit

To debug, modify the command above from step 3 to be:

`python -m debugpy debugpy --listen 0.0.0.0:6789 --wait-for-client manage.py test`

### specific tests - unit

To target a specific test, add the full class path of the test /after/ `test` in the manage.py command. For example:

`python -m debugpy --listen 0.0.0.0:6789 --wait-for-client manage.py test apps.dot_ext.tests.test_scopes.TestScopesBackendClass.test_get_available_scopes`

## integration testing

You'll need to exec into your running instance of bb-api to do this

1. Exec into bb-api
2. Run `python manage.py test --tag=integration` or `make integration-test`

### debugging - integration

Same as unit tests

### specific tests - integration

Same as unit tests

## selenium testing

For this, check the selenium/ subfolder
