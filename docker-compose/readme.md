# Local Docker Development

To begin developing locally, internal software engineers will need to obtain and copy the `bb2-local-client` certificate files in to the `docker-compose/certstore` location to support the connection to the BFD FHIR server.

To startup the Docker containerized BB2 server, run the following command: 

```
docker-compose up -d

```

Alternatively, to monitor BB2 server logging:

```
docker-compose up -d
docker-compose logs -f | grep web

```
press Ctrl C will stop monitor logging.

## Blue Button DB image migrations

DB image migrations is done in docker container before blue button server is started.
this is enabled by adding below line to .env:

```
DB_MIGRATIONS=true
```

the migration creates a super user with below attributes, can be customized in .env:

```
SUPER_USER_NAME=root
SUPER_USER_PASSWORD=blue123
SUPER_USER_EMAIL=bluebutton@example.com
```

if chose not to do db image migrations automatically, follow below steps:

set the flag to false before run docker-compose up:

```
DB_MIGRATIONS=false
```

If you're working with a fresh db image
the migrations have to be run.

```
docker-compose exec web docker-compose/migrate.sh

```

If any permissions errors are thrown try the following command,
then run the migrate script again:
```
docker-compose exec web chmod +x docker-compose/migrate.sh
```

## Running tests from your host

To run the Django unit tests, run the following command:

```
docker-compose exec web python runtests.py
```

You can run individual applications tests or tests with in a specific area as well.

The following are a few examples (drilling down to a single test):
```bash
docker-compose exec web python runtests.py apps.dot_ext.tests
```
```bash
docker-compose exec web python runtests.py apps.dot_ext.tests.test_templates
```
```bash
docker-compose exec web python runtests.py apps.dot_ext.tests.test_templates.TestDOTTemplates.test_application_list_template_override
```
Multiple arguments can be provided too:
```bash
docker-compose exec web python runtests.py apps.dot_ext.tests apps.accounts.tests.test_login
```


# Work on Windows

This requires the use of a linux sub system. This includes a choice of Cygwin, WSL, or VirtualBox + Linux.
Install the Docker Desktop on your Windows host, and set the DOCKER_HOST environment 
variable in linux sub system. Also enable the git configuration for proper EOL CRLF/LF 
convertion using the following command: 

```
git config --global core.autocrlf true

```
in case, with above git core.autocrlf setting, some steps e.g. migrate.sh still chokes (file not found etc.),
fix script manually, e.g. using dos2unix.

If needing to pass the docker compose environment variable, make a copy of the .env.example and
change it accordingly.

### In the .env file add the below hint to properly handle path:

```
COMPOSE_CONVERT_WINDOWS_PATHS=1
```

## Remote debugging BB2 server

Add the line below to the .env file to enable remote PTVSD debugging
of BB2 server in a docker container:

```
BB20_ENABLE_REMOTE_DEBUG=true
```

After BB2 server is up, ptvsd is listening on port 5678.
Afterward, attach to it from your IDE (e.g. VSCode) and put break 
points on the execution path. You can now start debugging.

Add the line below to the .env file to make ptvsd agent wait on attaching, before execute
bluebutton server, this is needed when debugging logic during bluebutton server bootstrap.

```
BB2_REMOTE_DEBUG_WAIT_ATTACH=true
```

## Remote debugging Blue Button unit tests

Run the docker-compose command below to start the unittests with PTVSD and for it to wait on port 6789 for the debugger to attach.
Attach to the unittests from an IDE (e.g. VSCode), then put break points in the test cases and debugging.

```
docker-compose up -d unittests

```

## Test and Verify Using Sample Clients

After the container is up, go to http://localhost:8000 (default) address location, and you will see the CMS Blue Button landing page,
Follow the documentation to create accounts, register applications, and other tasks in the local development environment. Note that some features, like email, work differently when running locally.  For example, a text version of an email is sent in to the main server log and is where you will find your signup confirmation activation link. 

You are also able to manually modify Django model objects when needed by using the Django ADMIN at: http://localhost:8000/admin.

To test if there is connectivity to the back end BFD FHIR server, go to the following URL at: http://localhost:8000/health/external.

###Test from clients:


* You can test from in the browser on the homepage using the testclient. This is located from the top of the page by clicking the link `testclient`
* You can test using one of our sample clients applications. See the related blog posts for more information: 
  * [Sample Client Applications](https://bluebutton.cms.gov/blog/Sample-Applications.html) 
  * [More Sample Client Applications](https://bluebutton.cms.gov/blog/More-Sample-Applications.html)
  * [Install a Django Client](https://bluebutton.cms.gov/blog/Installing-a-Django-client-application.html)

Make changes to configurations by following the sample clients instructions and test the end to end scenarios.

## Test with Sample Beneficiary

The following can be used to test FHIR resource calls using CURL commands. These use the sample beneficiary user `fred` that is setup when running the `migration.sh` script in the initial setup.

```
export ACCESS_TOKEN="sample-token-string"
export BENE_ID="-20140000008325"
export HOST="http://localhost:8000"

```

Get Pateint FHIR Resource json


```
curl --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/Patient/${BENE_ID}"

```

Get ExplanationOfBenefit FHIR Resource json

```
curl -k -v --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/ExplanationOfBenefit/?Patient=${BENE_ID}"

```
