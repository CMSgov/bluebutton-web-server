# Local Docker Development

To begin developing locally, internal software engineers will need to obtain and copy the `bb2-local-client` certificate files in to the `docker-compose/certstore` location to support the connection to the BFD FHIR server.

To startup the Docker containerized Blue Button 2.0 server run the following command: 

```
docker-compose up web
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

# Work on Windows

This requires the use of a linux sub system. This includes a choice of Cygwin, WSL, or VirtualBox + Linux.
Install the Docker Desktop on your Windows host, and set the DOCKER_HOST environment 
variable in linux sub system. Also enable the git configuration for proper EOL CRLF/LF 
convertion using the following command: 

```
git config --global core.autocrlf true

```

If needing to pass the docker compose environment variable, make a copy of the .env.example and
change it accordingly.

### In the .env file add the below hint to properly handle path:

```
COMPOSE_CONVERT_WINDOWS_PATHS=1
```

## Remote debugging Blue Button server

Add the line below to the .env file to enable remote PTVSD debugging
of Blue Button server in a docker container:

```
BB20_ENABLE_REMOTE_DEBUG=true
```

After the Blue Button server is up, ptvsd is listening on port 5678.
Afterward, attach to server from your IDE (e.g. VSCode) and put break 
points on the execution path. You can now start debugging.

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

To test if there is connectivity to the back end FHIR database server, go to the following URL at: http://localhost:8000/health/external.

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
curl --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/Patient/${BENE_ID}

```

Get ExplanationOfBenefit FHIR Resource json

```
curl -k -v --header "Authorization: Bearer ${ACCESS_TOKEN}"  "${HOST}/v1/fhir/ExplanationOfBenefit/?Patient=${BENE_ID}"

```
