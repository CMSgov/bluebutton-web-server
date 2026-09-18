# Obtain Prerequisites

It is possible to run the stack on localhost; we do not recommend it.

| Tool | Installation instructions | 
| -------- | -------- | 
| ZScaler | Ensure you are already connected to ZScaler: [How-to-Guide: Installing Zscaler on Mac OS (Contractors)](https://confluence.cms.gov/spaces/ODI/pages/1034031756/How-to-Guide+Installing+Zscaler+on+Mac+OS+Contractors)| 
| AWS CLI v2 | https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html <br> <strong>NOTE:</strong> It's recommended to use the GUI Installer. It's unsure at this point if you should either do the current user or all users option and it likely doesn't matter. If you just do the current user, you'll need to ensure you pick a location you can write to when going through the installation prompt (i.e. /Users/<company-id>). You'll then need to make sure that path is included in the following symlink commands that the aws instructions tell you to copy and paste. | 
| Git | Install [Git](https://git-scm.com/) if you don't have it |
| VS Code | Install [VSCode](https://code.visualstudio.com/download) or any other code editor of your choice |

## Podman Desktop
The following depicts the high-level changes of docker command flow after changing to podman desktop:

`Docker CLI -> DOCKR_HOST -> Podman Service (inside Podman Desktop/VM)`

We aren't using Docker Desktop (daemon + VM + socket) anymore because of licensing issues. We'll be using Podman (VM + socket) while still using the docker cli as the client. This will allow us to not have a ton of changes to the codebase by still being able to run docker commands within our startup scripts. Docker CLI commands work since they send API requests over a Unix socket (DOCKER_HOST) to Podman's service, which runs inside the VM and executes them. The checklist below is what you should follow to use Podman Desktop instead of Docker Desktop.

* Install Podman Desktop following these instructions starting at "Procedure"
  * Install Podman Desktop using the the .dmg file method
    * Podman Desktop is where you can view images, containers, volumes, etc.
  * Install Podman
  * Create a Podman Machine
    * The podman machine is necessary for installing the linux kernel environment because podman is a Linux tool
* Enable Docker Compatibility in Podman Desktop
  * Go to Settings → Preferences → Toggle "Docker Compatibility" on
* Download docker cli and docker compose plugin via homebrew
  * Run `brew install docker`
  * Run `brew install docker-compose  `
  * This is necessary to enable docker and docker compose as a client talking to the podman engine
* Edit docker config.json
  * Run `vim ~/.docker/config.json` (or open in your text editor of choice)
  * Copy and paste the following into your config.json:
  * ```json
	{ 
		"auths": {}, 
		"credsStore": "",
		"currentContext": "desktop-linux", 
		"cliPluginsExtraDirs": [ "/opt/homebrew/lib/docker/cli-plugins" ] 
	}
	```
	* The above gets rid of the docker desktop credStore (since we aren't using it anymore) and also adds configuration for the docker compose plugin directory
  * Save and Exit 
* Edit.zshrc file
  * Run `vim ~/.zshrc`
  * Add the following to the end: `export DOCKER_HOST=unix://$HOME/.local/share/containers/podman/machine/podman.sock`
  * Save and exit 
  * Ensure you run `source ~/.zshrc` to update the file
  * We need to add a docker host so that there's a socket connection from our docker commands to the podman engine server

## AWS

In order to configure AWS, you do not need to grab credentials; this is what kion is for. However, you do want to set some defaults in the config.

| Creating AWS Config File |
| -------- |
```bash
mkdir ~/.aws
touch ~/.aws/config
```

In the config, paste the following:

| AWS Config File |
| -------- |
```
[default]

region = us-east-1

output = json

[profile bluebutton-nonprod]

region = us-east-1
```

## Cloudtamer (Kion)

You can manually confirm whether or not you have the permissions you need for accessing systems. To do this, log into CMS Cloudtamer (Kion).

1. Log in to Cloudtamer (Kion)
    * https://cloudtamer.cms.gov/portal
2. Select the organizational units from the menu (OUs)
3. Search for “blue” — specifically, you’re looking for bluebutton-nonprod.

If you do not have access, tag your Program Manager. You will need both 

  * bluebutton-nonprod
  * bluebutton-prod

On the left, click “Projects,” and find the Blue Button non-prod project. Star it, so it shows up on your dashboard in the future.

## Install kion-cli

Kion provides secrets access; the CLI lets us pull those secrets via API for use in our dev and automations. The easiest way to install the CLI is via [Homebrew](https://brew.sh/). Ensure you also add homebrew to PATH following the Next Steps at the end of the install brew command. Then you can install kion-cli by doing the following:

| AWS Config File |
| -------- |
```bash
brew update

brew install kionsoftware/tap/kion-cli
```

### Configuration Needed

Create a .kion.yml in your home directory by doing a `touch ~/.kion.yml`

Paste in the following configuration into your.kion.yml. Ensure you fill in the actual account id. The favorites section isn't required but should make your life easier for authenticating with kion.

```
kion:
  url: https://cloudtamer.cms.gov
  idms_id: 5
  saml_metadata_file: https://idm.cms.gov/app/exk10wd8mvjHwLRKa298/sso/saml/metadata
  saml_sp_issuer: https://cloudtamer.cms.gov/api/v1/saml/auth
  disable_cache: false
favorites:
  - name: bbnp
    account: <replace-me-with-account-id>
    cloud_access_role: Blue Button Application Admin
    access_type: cli
```

Once you save this file, you can go into a repo and try to authenticate with kion doing a `kion s` . This will lead you to your browser where you will need to sign in with your CMS EUA ID and password. Once you sign in, you can close your browser and go back to your terminal and continue the selecting the project, account, and cloud access role.

# Ensure you Add an SSH Key to GitHub

Ensure you have an ssh key added to Github before trying to clone down the repo.

  * [Generating a New SSH Key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)
  * [Adding the New SSH Key your Github Account](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)

## Clone Down the Necessary Repos
| Clone Commands |
| -------- |
```bash
git clone git@github.com:CMSgov/bluebutton-web-server.git

git clone git@github.com:CMSgov/bluebutton-site-static.git

git clone git@github.com:CMSgov/cms-bb2-node-sdk.git

git clone git@github.com:CMSgov/cms-bb2-python-sdk.git

git clone git@github.com:CMSgov/bluebutton-sample-client-nodejs-react.git

git clone git@github.com:CMSgov/bluebutton-sample-client-python-react.git
```

### Create a .env file
Within the root of bluebutton-webserver repo, you can copy content from .env.example into a .env file [here](https://github.com/CMSgov/bluebutton-web-server/blob/master/.env.example).

### Create a .env.local file
Within the the dev.local folder of bluebutton-webserver repo, you can copy content from .env.local.example into a .env.local file [here](https://github.com/CMSgov/bluebutton-web-server/blob/master/ops/containers/bb-api/files/external/.env.local.example).

### Once you are done: running things day-to-day
There are some aspects of local development that are still impacted by being online and authenticated correctly.

<strong>Make sure you are on ZScaler</strong>

Generally, you'll need to be on ZScaler for active development. This is because you'll often be authenticating against either TEST or SBX environments, which suggest you'll be hitting test.medicare.gov for test users (e.g. BBUser00005 for V1/V2, or perhaps BBUser09003 for v3, as examples). This requires being on the VPN.

<strong>Run kion / grab certs</strong>

Kion grabs the creds for AWS. It would seem, for most development actions, that you should not need the creds. However, some devs have noticed that running the stack without having recently logged into kion and grabbing the certs can lead to issues. We are (at the moment) unclear if those certs change, how often, etc. So, running kion (and selecting appropriate values), followed by sourcing the certs is considered necessary for a consistent local dev/auth experience.

## Configuring your dev environment

First, download the ruff extension from VS Code extensions.

You will also set up ruff as a pre-commit hook. If you already have a venv, you can skip this step since our dev dependencies have pre-commit inside them already.

| Pre-Commit Commands|
| ------ |
```
python -m venv venv
source .venv/bin/activate # May be without the .
pip install -r requirements/requirements.dev.txt
```
Now install the hook:
| Install Git Hook |
| ------ |
```
# Install the git hook
pre-commit install
```

Now, whenever you try to commit to the repo, you will be prevented from committing if you have ruff errors!

To automatically format your files on save (highly recommended), do the following:

* Press Cmd + Shft + P
* Type Open User Settings  and select it
* Add the following to your VS Code User Settings file:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

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

## Configuring your dev environment

First, download the ruff extension from VS Code extensions.

You will also set up ruff as a pre-commit hook. If you already have a venv, you can skip this step since our dev dependencies have pre-commit inside them already.

| Pre-Commit Commands|
| ------ |
```
python -m venv venv
source .venv/bin/activate # May be without the .
pip install -r requirements/requirements.dev.txt
```
Now install the hook:
| Install Git Hook |
| ------ |
```
# Install the git hook
pre-commit install
```

Now, whenever you try to commit to the repo, you will be prevented from committing if you have ruff errors!

To automatically format your files on save (highly recommended), do the following:

* Press Cmd + Shft + P
* Type Open User Settings  and select it
* Add the following to your VS Code User Settings file:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

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

## migrating and collecting static files

If it is the first time you run the stack, you will need to run migrations (in order to initialize the database) and collectstatic (in order to build the CSS assets and move them to the mocked S3 bucket).

Run the migrate and collectstatic management commands from the root of bluebutton-web-server:

```bash
make migrate
make collectstatic
```

## run the stack

Next, you run the stack. You need to be in an active Kion session for this to work.

| Starting Stack Commands |
| -------- |
```
# Run these in order when spinning up the stack for the first time

kion s # You will need this to grab the credentials from AWS

cd ./ops/containers  # or run from project root, the Makefile there references the one in ops/containers

make build-local

make migrate

make collectstatic

make run-local bfd=sbx auth=live # OR the one below

make run-local bfd=test auth=live daemon=1

# OR if zscaler is causing 500 errors, set auth=mock
```
You should be able to interact with the stack at localhost:8000, either through the test client, or with Postman (see [Using Postman with Blue Button](https://confluence.cms.gov/spaces/BB2/pages/741508640/Using+Postman+with+Blue+Button)).

Note:
```bash
make run-local bfd="..." auth="..." sls="..." CAN_INTEGRATION_TEST="..."
```

where `bfd` is `local`, `test`, or `sbx`, `auth` is `live` or `mock`, `sls` is `test` or `imp`, `CAN_INTEGRATION_TEST` is `true` or `false`. If you do not provide any values and just run `make run-local`, the default is to use `bfd=test auth=live sls=test CAN_INTEGRATION_TEST=false`.

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

## handling migrations

Before logging in to a running stack, ensure you ran the stack with READ_ONLY set to false like below:

```
make run-local bfd=test auth=live READ_ONLY=false
```

This will allow you to make a new migration and not run into any read-only file system issues.

After altering models, open a new terminal and log into a running stack using
`docker exec -u root -it <contatiner_id> bash` (for root permissions), and then run

```
python manage.py makemigrations
```

This will generate the migrations file. If you then want to apply those, exit the container and run

```
make migrate
```

to run the Makefile target that stands up the stack and runs `python manage.py migrate`.

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

## testing

Ensure you have your launch.json within the .vscode folder at the project's root directory updated to the following:
  * Create a launch.json if it is not there

```bash
	{
	    // Use IntelliSense to learn about possible attributes.
	    // Hover to view descriptions of existing attributes.
	    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
	    "version": "0.2.0",
	    "configurations": [
	        {
	            "name": "API",
	            "type": "debugpy",
	            "request": "attach",
	            "connect": {
	                "host": "0.0.0.0",
	                "port": 5678
	            },
	            "pathMappings": [
	                {
	                    "localRoot": "${workspaceFolder}",
	                    "remoteRoot": "."
	                }
	            ]
	        },
	        {
	            "name": "Unit Test",
	            "type": "debugpy",
	            "request": "attach",
	            "connect": {
	                "host": "0.0.0.0",
	                "port": 6789
	            },
	            "pathMappings": [
	                {
	                    "localRoot": "${workspaceFolder}",
	                    "remoteRoot": "."
	                }
	            ]
	        },
			{
	            "name": "Selenium Test",
	            "type": "debugpy",
	            "request": "attach",
	            "connect": {
	                "host": "0.0.0.0",
	                "port": 7890
	            },
	            "pathMappings": [
	                {
	                    "localRoot": "${workspaceFolder}",
	                    "remoteRoot": "."
	                }
	            ]
	        }
	    ]
	}
```
You can test this is now working by starting up your debugger in the RUN AND DEBUG  tab in vs code by hitting the RUN button on the API config option. Then set a breakpoint wherever you would like to test and hit that api call in localhost.

Example: Putting a breakpoint in views/authoriaztion.py and going to http://localhost:8000/testclient

### unit testing

Unit testing needs to be ran outside of the container, otherwise you run into issues with port mappings.

#### prerequisites

1. Ensure you have python 3.12 installed locally
2. pip install pip==25.3
3. pip install pip-tools setuptools

#### running unit tests

Setup your local venv (or whatever flavor of local python environment) and install the dev dependencies

1. Activate your environment
    * `python -m venv venv` (or if using uv `uv venv --python 3.12`)
    * `source venv/bin/activate`
2. Install the requirements into the environment `pip install -r requirements/requirements.dev.txt`
3. Run `pytest -m 'not integration'` or `make unit-test`

#### debugging - unit

Make sure you have your launch.json updated like above. To debug, modify the command above from step 3 to be:

`python -m debugpy --listen 0.0.0.0:6789 --wait-for-client -m pytest -m 'not integration'`

After running this in the terminal, navigate to the `Run and Debug` extension of VS Code and run the `Unit Test` play button. You can set breakpoints accordingly in different tests to test functionality and stop at different moments.

#### specific tests - unit

To target a specific test, add the file path of the test and the test name. If the test is within a class, also include the class name. For example:

`pytest apps/dot_ext/tests/test_scopes.py::TestScopesBackendClass::test_get_available_scopes`

Note that if the test is not within a class, you can just use ::test_name

### integration testing

You'll need to exec into your running instance of bb-api to do this

1. Exec into bb-api
  * `docker exec -it containers-bb-api-1 bash`
    * If that is not your container name, you can check what it is while it is up via `docker stats`
  * Or you can 'exec' via the Terminal tab in Podman Desktop
2. Run `pytest -m 'integration'` or `make integration-test`

If you want to run the CAN integration test, you will need to make sure that you run `make run-local CAN_INTEGRATION_TEST=true` when starting the container. This will run a selenium container since that is required in order to run the CAN integration test. You can then exec into bb-api and run `pytest apps/fhir/bluebutton/tests/test_CAN_integration.py` to run that specific test on its own or `make integration-test` to run all the integration tests.

#### debugging - integration

Same as unit tests

#### specific tests - integration

Same as unit tests

### selenium testing

For this, check the README in ops/containers/selenium [here](https://github.com/CMSgov/bluebutton-web-server/blob/master/ops/containers/selenium/README.md)
