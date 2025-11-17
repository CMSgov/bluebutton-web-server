# containerized local development

The containerized local build should provide a local development experience that is

1. not in the way of developing new features
1. allows developers to be confident in the code they develop and ship
1. consistent with production-like environments (as much as possible)

These tools assume you are a developer working on the project, and have access to the VPN and other systems.

## pre-requisites

It is assumed you have a *NIX-like shell, and have the ability to run GNU Make or a reasonable fascimilie thereof. 

A Mac, out-of-the-box, should "just work," as well as an Intel-based Linux host. Under Windows, it is assumed that WSL2 would provide an environment that would work.

### configuring `kion`

You should already have a `.kion.yaml` in your home directory. If not, follow the [local desktop development](https://confluence.cms.gov/spaces/BB2/pages/484224999/Local+Desktop+Development) onboarding docs to set up Cloudtamer/`kion`.

You need to add an alias for this tooling to work.

```
favorites:
  - name: BB2-NON-PROD
    account: <account-number>
    cloud_access_role: <cloud-access-role>
    access_type: cli
```

If you already have some aliases, you can just add this one to the list. The account number and cloud access role can be obtained from the Cloudtamer dashboard. The alias **must** be named `BB2-NON-PROD` for these tools to work.

## to start

Copy `.env.local.example` to `.env.local`. You probably don't *have to* edit anything, but you can if you want.

## setting local environment variables

`.env.local` is pre-configured with variables that should "just work" in any local development environment.

At the top of the file are variables that a developer may want to fiddle with. Specifically:

* BB20_ENABLE_REMOTE_DEBUG=true
* BB20_REMOTE_DEBUG_WAIT_ATTACH=false
* RUN_ONLINE_TESTS=true

These variables control the debugger and whether we run tests that require a live connection to BFD in `TEST` and `SBX` environments. The latter is defaulted to `true` to ensure test coverage completeness when developing locally. The local dev tools help automate the process of testing against the online `test` and `sbx` environments.

## building local image(s)

The first step is to build the local containers. From the root of the tree, or from within `dev-local`, run 

```
make build-local
```

This should build the image `bb-local:latest`.

Building the image is only necessary when the `requirements/requirements.txt` or `requirements/requirements.dev.txt` files change. Those requirements get baked into the image; changes to application code should be picked up via dynamic reload during normal development.

## running the local image

Next, run the stack.

### running locally / mocking MSLS

To run the stack locally,

```
make run-local ENV=local
```

This will launch the stack with no connection to live environments, and it will use the mocked MSLS tooling.

### running against `test`

When launched with

```
make run-local TARGET=test
```

the tooling obtains and sources credentials for running against our `test` environment.

### running against `sbx`

Similarly,

```
make run-local TARGET=sbx
```

runs against SBX. 

#### what is the difference?

`test` and `sbx` hit different BFD servers, with different data.

### what do these run targets do?

In a nutshell:

1. Run `kion f BB2-NON-PROD` to authenticate/obtain AWS credentials.
1. Obtain certificates for the remote environment (if you selected `test` or `sbx`)
1. `docker compose --profile mock-sls up` for `local`, `docker compose --profile slsx up` for live envs.

## future work

Once this is in place, it is easy to script/add Makefile targets for some additional tools. For example, we could have a menu driven script to...

1. load synthetic test data (akin to [this](https://github.com/GSA-TTS/FAC/blob/main/backend/util/load_public_dissem_data/manage_local_data.bash))
1. create/remove admin users
1. Test database dump/load
1. Run Selenium tests
1. ...

can be easily added, and leveraged in future containerization/devops work.

## paths and variables

This set of tools creates a new directory (`.bb2`) in the developers $HOME. This is treated as a kind of "BB2 config directory" by this local automation tooling. It uses this (new) directory for the simple reason that there are things we do not want floating around in the source tree, if we can avoid it. Specifically, we do not want to download the certs for `test` and `sbx` into the git tree.

## notes



