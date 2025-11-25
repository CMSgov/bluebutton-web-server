# containerized local development

The containerized local build should provide a local development experience that is

1. not in the way of developing new features
1. allows developers to be confident in the code they develop and ship
1. consistent with production-like environments (as much as possible)

These tools assume you are a developer working on the project, and have access to the VPN and other systems.

## TL;DR

```
make build-local
```

And then

```
make run-local bfd=test auth=live daemon=1
```

or maybe

```
make run-local bfd=sbx auth=live
```


## pre-requisites

It is assumed you have a *NIX-like shell, and have the ability to run GNU Make or a reasonable fascimilie thereof. 

A Mac, out-of-the-box, should "just work," as well as an Intel-based Linux host. Under Windows, it is assumed that WSL2 would provide an environment that would work.

### configuring `kion`

*To run the tools, you must be in a `kion` shell. What follows is a way to set up an alias that makes running the correct configuration easier. You can also run `kion stak` or `kion s` and navigate the menus to achieve a similar result.*

You should already have a `.kion.yaml` in your home directory. If not, follow the [local desktop development](https://confluence.cms.gov/spaces/BB2/pages/484224999/Local+Desktop+Development) onboarding docs to set up Cloudtamer/`kion`.

You need to add an alias in the previously mentioned .kion.yaml for this tooling to work.
Open .kion.yaml with something like:

```
code ~/.kion.yml 
```

Then add the alias as:

```
favorites:
  - name: bbnp
    account: <account-number>
    cloud_access_role: <cloud-access-role>
    access_type: cli
```

If you already have some aliases, you can just add this one to the list. The account number and cloud access role can be obtained from the Cloudtamer dashboard. This is not strictly necessary, as the tooling cannot automate a `kion` call *and* then continue, as `kion` opens a new shell. However, it is much easier (and, for this documentation, the preferred method) to invoke

```
kion f bbnp
```

than to navigate a menu structure. You may ultimately choose a shorter alias, e.g. `kion f bbnp`.

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

This should build the container image for `bb-local:latest`, the Selenium image, and the MSLS image.

Building the images is only necessary when the `requirements/requirements.txt` or `requirements/requirements.dev.txt` files change. Those requirements get baked into the image; changes to application code should be picked up via dynamic reload during normal development.

## running the local image

Next, run the stack.

### running the stack

There are four possible ways to run the stack.

```
make run-local bfd=<bfd-option> auth=<auth-option>
```

For example, to run against `test` with a live SLSX exchange:

```
make run-local bfd=test auth=live
```

Each combination has different implications. Only some make sense at this time (Nov '25):

|  | auth=mock | auth=live |
| --- | --- | --- |
| **bfd=local** | local unit tests | testing SLSX sequences |
| **bfd=test** | ⛔ | Full-up against `test` | 
| **bfd=sbx** | ⛔ | Full-up against `sbx` | 

* `local/mock`: This makes sense for running unit tests; only local tests will run in this configuration.
* `local/live`: Manual testing of SLSX sequences should be able to be performed with this combination. No BFD/FHIR URLs are set, though, which may break things.
* `test/mock`: *Not a valid condition*; a mock authentication will not work with a live server.
* `test/live`: Live SLSX exchanges with medicare.gov and calls against the `test` BFD environment.
* `sbx/mock`: *Not a valid condition*.
* `sbx/live`: Live SLSX exchanges and calls against the `sbx` BFD environment.


### running daemonized

You cann add `daemon=1` to any of the above commands, and the stack will run in the background.

For example:

```
make run-local bfd=test auth=live daemon=1
```

### running against `test`

When launched with

```
make run-local bfd=test auth=live
```

the tooling obtains and sources credentials for running against our `test` environment.

### running against `sbx`

Similarly,

```
make run-local bfd=sbx auth=live
```

runs against SBX. 

#### what is the difference?

`test` and `sbx` hit different BFD servers, with different data.

### what do these run targets do?

In a nutshell:

1. Run `kion f bbnp` to authenticate/obtain AWS credentials.
1. Obtain certificates for the remote environment (if you selected `test` or `sbx`)
1. Pass appropriate env vars through to the app, based on choices.

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




