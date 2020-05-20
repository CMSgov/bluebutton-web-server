# Local Docker Development

Developing locally with docker containerized blue button server, just run: 

```
docker-compose up web
```

If you're working with a fresh db image
the migrations have to be run.

```
docker-compose exec web docker-compose/migrate.sh

```

if any permissions errors are thrown try
docker-compose exec web chmod +x docker-compose/migrate.sh
then run the migrate script again

## Running tests from your host

```
# run tests
docker-compose exec web python runtests.py
```

# Work on Windows:

It requires linux sub system: Cygwin, WSL, VirtualBox + Linux
Install Docker Desktop on host (Windows), and set DOCKER_HOST environment 
variable in linux sub system, enable git configuration for proper EOL CRLF/LF 
convertion: 

```
git config --global core.autocrlf true

```

If need to pass docker compose environment, make a copy of .env.example, and
change it accordingly:

### In .env add below hint to properly handle path:

COMPOSE_CONVERT_WINDOWS_PATHS=1

## Remote debugging blue button server:

Add below to .env to enable remote ptvsd debugging
of blue button server in docker container

```
BB20_ENABLE_REMOTE_DEBUG=true
```

After blue button server is up, ptvsd is listening on port 5678,
Attach to blue button server from IDE, e.g. VSCode and put break 
points on execution path, and start debugging.

## Remote debugging blue button unit tests

Run below docker compose command to start unittests with ptvsd wait on port 6789 for debugger to attach,
Attach to unittests from IDE, e.g. VSCode and put break points in test cases, and debugging.

```
docker-compose up -d unittests

```

## Test and Verify Using Sample Clients

After container is up, go to localhost:8000 (default) and you will see CMS Blue Button landing page,
follow documentation to create account, register applications, etc., note, on a local development environment, email might not be properly set, so confirmation email might not be received, and hence account activation needs to
be done manually by going to localhost:8000/admin and activate it.

Test from clients:


* Test from in browser testclient - from top of developer sandbox click link 'testclient'
* Test from CMS Blue Button Sample Clients:
  * Ruby on Rails Sample Client: [Blue Button Sample Client Rails](https://github.com/CMSgov/bluebutton-sample-client-rails) 
  * Django Sample Client: [Blue Button Sample Client Django](https://github.com/CMSgov/bluebutton-sample-client-django)

Make changes to configurations following sample clients instructions and test the end to end scenarios.

## Test with Sample Beneficiary

```
export ACCESS_TOKEN="sample-token-string"
export BENE_ID="-20140000008325"
export HOST="http://localhost:8000"

```

Get Pateint FHIR Resource json


```
curl --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/Patient/${BENE_ID}

```

Get ExplanationOfBenefit FHIR Resource json

```
curl -k -v --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/ExplanationOfBenefit/?Patient=${BENE_ID}"

```